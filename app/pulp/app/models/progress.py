"""
Django models related to progress reporting
"""
from gettext import gettext as _
import logging

from django.db import models

from pulp.tasking import util
from pulp.app.models import Model, Task

_logger = logging.getLogger(__name__)


class ProgressReport(Model):
    """
    A base model for all progress reporting.

    All progress reports have a message, state, and are related to a Task.

    Fields:

        message (models.TextField): short message for the progress update, typically
            shown to the user. (required)
        state (models.TextField): The state of the progress update. Defaults to `WAITING`. This
            field uses a limited set of choices of field states. See `STATES` for possible states.
        total: (models.IntegerField) The total count of items to be handled by the ProgressBar
            (required)
        done (models.IntegerField): The count of items already processed. Defaults to 0.
        suffix (models.TextField): Customizable suffix rendered with the progress report
            See `the docs <https://github.com/verigak/progress>`_. for more info.

    Relations:

        task: The task associated with this progress report. If left unset when save() is called
            it will be set to the current task_id.
    """
    WAITING = 'waiting'
    SKIPPED = 'skipped'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELED = 'canceled'
    STATES = (
        (WAITING, 'Waiting'),
        (SKIPPED, 'Skipped'),
        (RUNNING, 'Running'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (CANCELED, 'Canceled')
    )
    message = models.TextField()
    state = models.TextField(choices=STATES, default=WAITING)

    total = models.IntegerField(null=True)
    done = models.IntegerField(default=0)

    task = models.ForeignKey("Task", on_delete=models.CASCADE)
    suffix = models.TextField(default='')

    def save(self, *args, **kwargs):
        """
        Auto-set the task_id if running inside a task

        If the task_id is already set it will not be updated. If it is unset and this is running
        inside of a task it will be auto-set prior to saving.

        args (list): positional arguments to be passed on to the real save
        kwargs (dict): keyword arguments to be passed on to the real save
        """
        if self.task_id is None:
            self.task_id = Task.objects.get(id=util.get_current_task_id())
        super(ProgressReport, self).save(*args, **kwargs)

    def __enter__(self):
        """
        Saves the progress report state as RUNNING
        """
        self.state = self.RUNNING
        self.save()

    def __exit__(self, type, value, traceback):
        """
        Update the progress report state to COMPLETED or FAILED.

        If an exception occurs the progress report state is saved as FAILED and the exception is
        not suppressed. If the context manager exited without exception the progress report state
        is saved as COMPLETED.

        See the context manager documentation for more info on __exit__ parameters
        """
        if type is None:
            self.state = self.COMPLETED
            self.save()
        else:
            self.state = self.FAILED
            self.save()


class ProgressSpinner(ProgressReport):
    """
    Shows progress reporting when the count of items is not known.

    Plugin writers should create these objects to show progress reporting of a single step or
    aspect of work which has a name and a state. For example:

        >>> ProgressSpinner(message='Publishing Metadata')  # default state is 'waiting'

        >>> ProgressSpinner(message='Publishing Metadata', state='running')  # specify 'running'

    Update the state to COMPLETED and save it:

        >>> metadata_progress = ProgressSpinner(message='Publishing Metadata', state='running')
        >>> metadata_progress.state = 'completed'
        >>> metadata_progress.save()

    The ProgressSpinner() is a context manager that provides automatic state transitions and saving
    for the RUNNING COMPLETED and FAILED states. Use it as follows:

        >>> spinner = ProgressSpinner('Publishing Metadata')
        >>> spinner.save() # spinner is saved as 'waiting'
        >>> with spinner:
        >>>     # spinner is saved as 'running'
        >>>     publish_metadata()
        >>> # spinner is saved as 'completed' if no exception is raised or 'failed' otherwise

    You can also use this short form which handles all necessary save() calls:

        >>> with ProgressSpinner('Publishing Metadata'):
        >>>     publish_metadata()

    ProgressSpinner objects are associated with a Task and auto-discover and populate the task id
    when saved.
    """

    class Meta:
        proxy = True


class ProgressBar(ProgressReport):
    """
    Shows progress reporting when the count of items is known.

    Plugin writers should create these objects to show progress reporting of a single step or
    aspect of work which has a name and state along with total and done counts. For example:

        >>> ProgressBar(message='Publishing files', total=23)  # default: state='waiting' and done=0

        >>> ProgressBar(message='Publishing files', total=23, state='running')  # specify the state
        >>> ProgressBar(message='Publishing files', total=23, done=16)  # already completed 16

    Update the state to COMPLETED and save it:

        >>> progress_bar = ProgressBar('Publishing files', total=23, state='running')
        >>> progress_bar.state = 'completed'
        >>> progress_bar.save()

    The ProgressBar() is a context manager that provides automatic state transitions and saving for
    the RUNNING COMPLETED and FAILED states. The increment() method can be called in the loop as
    work is completed. Use it as follows:

        >>> progress_bar = ProgressBar(message='Publishing files', total=len(files_iterator))
        >>> progress_bar.save()
        >>> with progress_bar:
        >>>     # progress_bar saved as 'running'
        >>>     for file in files_iterator:
        >>>         handle(file)
        >>>         progress_bar.increment()  # increments and saves
        >>> # progress_bar is saved as 'completed' if no exception or 'failed' otherwise

    A convenience method called iter() allows you to avoid calling increment() directly:

        >>> progress_bar = ProgressBar(message='Publishing files', total=len(files_iterator))
        >>> progress_bar.save()
        >>> with progress_bar:
        >>>     for file in progress_bar.iter(files_iterator):
        >>>         handle(file)

    You can also use this short form which handles all necessary save() calls:

        >>> with ProgressBar(message='Publishing files', total=len(files_iterator)) as pb:
        >>>     for file in pb.iter(files_iterator):
        >>>         handle(file)

    ProgressBar objects are associated with a Task and auto-discover and populate the task id when
    saved.

    When using threads to update a ProgressBar in parallel, it is recommended that all threads
    share the same in-memory instance. Django does not synchronize in-memory model instances, so
    multiple instances of a specific ProgressBar will diverge as they are written to from separate
    threads.
    """

    class Meta:
        proxy = True

    def increment(self):
        """
        Increment done count and save the progress bar.

        This will increment and save the self.done attribute which is useful to put into a loop
        processing items.
        """
        self.done += 1
        if self.done > self.total:
            _logger.warning(_('Too many items processed for ProgressBar %s') % self.message)
        self.save()

    def iter(self, iter):
        """
        Iterate and automatically call increment().

            >>> progress_bar = ProgressBar(message='Publishing files', total=23)
            >>> progress_bar.save()
            >>> for file in progress_bar.iter(files_iterator):
            >>>     handle(file)

        Args:
            iter (iterator): The iterator to loop through while incrementing

        Returns:
            generator of ``iter`` argument items
        """
        for x in iter:
            yield x
            self.increment()