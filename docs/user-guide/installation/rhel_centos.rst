CentOS and RHEL
===============

This page contains installation instructions for CentOS and RHEL.
The :ref:`platform-support-policy` defines platforms are currently supported.


Repositories
------------

Pulp
^^^^

Download the appropriate repo definition file from the Pulp repository:

 * RHEL 6 Server: https://repos.fedorapeople.org/repos/pulp/pulp/rhel6-pulp.repo
 * RHEL: https://repos.fedorapeople.org/repos/pulp/pulp/rhel-pulp.repo

.. note::
   The RHEL repo contains the latest stable Pulp release. This has the pulp packages for RHEL 7+,
   and the pulp-consumer and pulp-nodes packages for RHEL 6 and 7.

   The RHEL 6 repo contains the the Pulp 2.11 packages. Pulp 2.11 is the last supported release
   for EL6. EL6 users are encouraged to upgrade their Pulp environments to EL7.


EPEL for RHEL & CentOS
^^^^^^^^^^^^^^^^^^^^^^

In addition to the Pulp repo file, the EPEL repositories are required to install dependencies for
RHEL and CentOS systems. Following commands will add the appropriate repositories for RHEL/CentOS 6
and 7 respectively:

EPEL 6::

   $ sudo yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

EPEL 7::

   $ sudo yum install http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

.. note::
   EPEL requires users of RHEL 6.x to enable the ``optional`` repository,
   and users of RHEL 7.x to additionally enable the ``extras`` repository.
   Details are described
   `here <https://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F>`_.


Message Broker
^^^^^^^^^^^^^^

Qpid is the default message broker for Pulp, and is the broker used in this guide.

See the `Qpid packaging docs <http://qpid.apache.org/packages.html>`_ for information on
where to get Qpid packages for your OS.

If you would like to use RabbitMQ instead, see the
`RabbitMQ installation docs <http://www.rabbitmq.com/download.html>`_.

.. _server_installation:


Server
------

#. You must provide a running MongoDB instance for Pulp to use. You can use the same host that you
   will run Pulp on, or you can give MongoDB its own separate host if you like. You can even use
   MongoDB replica sets if you'd like to have higher availability. For yum based systems, you can
   install MongoDB with this command::

    $ sudo yum install mongodb-server

   You need mongodb-server with version >= 2.4 installed for Pulp server. MongoDB 2.x reached its EOL.
   It is encouraged to use MongoDB 3.x for performance reasons, the recommended version is >= 3.4.
   `Installation instructions <https://docs.mongodb.com/v3.6/tutorial/install-mongodb-on-red-hat/>`_
   can be found in the MongoDB documentation.

   It is highly recommended that you `configure MongoDB to use SSL`_. If you are using
   Mongo's authorization feature, you  will need to grant the ``readWrite`` and ``dbAdmin`` roles
   to the user you provision for Pulp to use. The ``dbAdmin`` role allows Pulp to create collections
   and install indices on them.

   After installing MongoDB, you should configure it to start at boot and start it. For Upstart
   based systems::

    $ sudo service mongod start
    $ sudo chkconfig mongod on

   For systemd based systems::

    $ sudo systemctl enable mongod
    $ sudo systemctl start mongod

   .. warning::
      On new MongoDB installations, MongoDB takes some time to preallocate large files and will not
      accept connections until it finishes. When this happens, Pulp will wait for MongoDB to
      become available before starting.

   .. _configure MongoDB to use SSL: http://docs.mongodb.org/v2.4/tutorial/configure-ssl/#configure-mongod-and-mongos-for-ssl

#. You must also provide a message bus for Pulp to use. Pulp will work with Qpid or RabbitMQ, but
   is tested with Qpid, and uses Qpid by default. This can be on the same host that you will
   run Pulp on, or elsewhere as you please. To install Qpid on a yum based system, use
   this command::

    $ sudo yum install qpid-cpp-server qpid-cpp-server-linearstore

   Pulp uses the ``ANONYMOUS`` Qpid authentication mechanism by default. To
   enable username/password-based ``PLAIN`` broker authentication, you will need
   to configure SASL with a username/password, and then configure Pulp to use that
   username/password. Refer to the Qpid docs on how to configure username/password
   authentication using SASL. Once the broker is configured, configure Pulp according
   to the docs on using
   :ref:`Pulp with Qpid and username/password authentication <pulp-broker-qpid-with-username-password>`.

   The server can be *optionally* configured so that it will connect to the broker using SSL by following the steps
   defined in the :ref:`Qpid SSL Configuration Guide <qpid-ssl-configuration>`. By default, Pulp
   does not expect to use SSL and will connect to the broker using a plain TCP connection to localhost.

   After installing and configuring Qpid, you should configure it to start at boot and start it. For
   Upstart based systems::

    $ sudo service qpidd start
    $ sudo chkconfig qpidd on

   For systemd based systems::

    $ sudo systemctl enable qpidd
    $ sudo systemctl start qpidd

#. Install the Pulp server, task workers, and their dependencies. For Pulp installations that use
   Qpid, install Pulp server using::

    $ sudo yum install pulp-server python-gofer-qpid python2-qpid qpid-tools

   .. note::
      For RabbitMQ installations, install Pulp server without any Qpid specific libraries.
      You may need to install additional RabbitMQ dependencies manually.

#. Also install support for different content via plugins::

    $ sudo yum install pulp-rpm-plugins pulp-puppet-plugins pulp-docker-plugins

#. Edit ``/etc/pulp/server.conf``. Most defaults will work, but these are sections you might
   consider looking at before proceeding. Each section is documented in-line.

   * **email** if you intend to have the server send email (off by default)
   * **database** if your database resides on a different host or port. It is strongly recommended
     that you set ssl and verify_ssl to True.
   * **messaging** if your message broker for communication between Pulp components is on a
     different host or if you want to use SSL. For more information on this section refer to the
     :ref:`Pulp Broker Settings Guide <pulp-broker-settings>`.
   * **tasks** if your message broker for asynchronous tasks is on a different host or if you want
     to use SSL. For more information on this section refer to the
     :ref:`Pulp Broker Settings Guide <pulp-broker-settings>`.
   * **server** if you want to change the server's URL components, hostname, or default credentials

#. Generate RSA key pair and SSL CA certificate::

   $ sudo pulp-gen-key-pair
   $ sudo pulp-gen-ca-certificate

#. Initialize Pulp's database. It is important that the broker is running before initializing
   Pulp's database. It is also important to do this before starting Apache or any Pulp services.
   The database initialization needs to be run as the ``apache`` user, which can be done by
   running::

   $ sudo -u apache pulp-manage-db

   .. note::
      If Apache or Pulp services are already running, restart them after running the
      ``pulp-manage-db`` command.

   .. warning::
      It is recommended that you configure your web server to refuse SSLv3.0. In Apache, you can do
      this by editing ``/etc/httpd/conf.d/ssl.conf`` and configuring the ``SSLProtocol`` directive
      like this::

         `SSLProtocol all -SSLv2 -SSLv3`

  .. warning::
     It is recommended that the web server only serves Pulp services.

#. Start Apache httpd and set it to start on boot. For Upstart based systems::

    $ sudo service httpd start
    $ sudo chkconfig httpd on

   For systemd based systems::

    $ sudo systemctl enable httpd
    $ sudo systemctl start httpd

   .. _distributed_workers_installation:

#. Pulp has a distributed task system that uses `Celery <http://www.celeryproject.org/>`_.
   Begin by configuring, enabling and starting the Pulp workers. To configure the workers, edit
   ``/etc/default/pulp_workers``. That file has inline comments that explain how to use each
   setting. After you've configured the workers, it's time to enable and start them. For Upstart
   systems::

      $ sudo chkconfig pulp_workers on
      $ sudo service pulp_workers start

   For systemd systems::

      $ sudo systemctl enable pulp_workers
      $ sudo systemctl start pulp_workers

   .. note::

      The pulp_workers systemd unit does not actually correspond to the workers, but it runs a
      script that dynamically generates units for each worker, based on the configured concurrency
      level. You can check on the status of those generated workers by using the
      ``systemctl status`` command. The workers are named with the template
      ``pulp_worker-<number>``, and they are numbered beginning with 0 and up to
      ``PULP_CONCURRENCY - 1``. For example, you can use ``sudo systemctl status pulp_worker-1`` to
      see how the second worker is doing.

#. There are two more services that need to be running.

   On some Pulp system, configure, start and enable the Celerybeat process. This process performs a
   job similar to a cron daemon for Pulp. Edit ``/etc/default/pulp_celerybeat`` to your liking, and
   then enable and start it. Multiple instances of ``pulp_celerybeat`` may run concurrently, which
   will make the Pulp installation more failure tolerant. For Upstart::

      $ sudo chkconfig pulp_celerybeat on
      $ sudo service pulp_celerybeat start

   For systemd::

      $ sudo systemctl enable pulp_celerybeat
      $ sudo systemctl start pulp_celerybeat

   Lastly, a ``pulp_resource_manager`` process must be running in the installation. This process
   acts as a task router, deciding which worker should perform certain types of tasks. As with
   ``pulp_celerybeat``, multiple instances of ``pulp_resource_manager`` may be run concurrently on
   separate hosts to increase fault tolerance, however, only one instance will ever be active at a
   time. Should the active instance become unavailable, another instance will take over after some
   delay.

   Edit ``/etc/default/pulp_resource_manager`` to your liking. Then, for upstart::

      $ sudo chkconfig pulp_resource_manager on
      $ sudo service pulp_resource_manager start

   For systemd::

      $ sudo systemctl enable pulp_resource_manager
      $ sudo systemctl start pulp_resource_manager


Admin Client
------------

The Pulp Admin Client is used for administrative commands on the Pulp server,
such as the manipulation of repositories and content. The Pulp Admin Client can
be run on any machine that can access the Pulp server's REST API, including the
server itself. It is not a requirement that the admin client be run on a machine
that is configured as a Pulp consumer.

Pulp admin commands are accessed through the ``pulp-admin`` script.


1. Install the Pulp admin client and plugin packages:

::

  $ sudo yum install pulp-admin-client pulp-rpm-admin-extensions \
  pulp-puppet-admin-extensions pulp-docker-admin-extensions

2. Update the admin client configuration to point to the Pulp server. Keep in mind
   that because of the SSL verification, this should be the fully qualified name of the server,
   even if it is the same machine (localhost will not work with the default apache
   generated SSL certificate). Regardless, the "host" setting below must match the
   "CN" value of the server's HTTP SSL certificate.
   This change is made globally to the ``/etc/pulp/admin/admin.conf`` file, or
   for one user in ``~/.pulp/admin.conf``:

::

  [server]
  host = localhost.localdomain


.. _consumer_installation:

Consumer Client And Agent
-------------------------

The Pulp Consumer Client is present on all systems that wish to act as a consumer
of a Pulp server. The Pulp Consumer Client provides the means for a system to
register and configure itself with a Pulp server. Additionally, the Pulp Consumer
Client runs an agent that will receive messages and commands from the Pulp server.

Pulp consumer commands are accessed through the ``pulp-consumer`` script. This
script must be run as root to permit access to add references to the Pulp server's
repositories.

1. For environments that use Qpid, install the Pulp consumer client, agent packages, and Qpid
specific consumer dependencies with one command by running:

::

   $ sudo yum install pulp-consumer-client pulp-rpm-consumer-extensions \
   pulp-puppet-consumer-extensions pulp-agent pulp-rpm-handlers pulp-rpm-yumplugins \
   pulp-puppet-handlers python-gofer-qpid


.. note::

     For RabbitMQ installations, install ``python-gofer-amqp`` instead of ``python-gofer-qpid``.


2. Update the consumer client configuration to point to the Pulp server. Keep in mind
   that because of the SSL verification, this should be the fully qualified name of the server,
   even if it is the same machine (localhost will not work with the default Apache
   generated SSL certificate). Regardless, the "host" setting below must match the
   "CN" value of the server's HTTP SSL certificate.
   This change is made to the ``/etc/pulp/consumer/consumer.conf`` file:

::

  [server]
  host = localhost.localdomain


3. The agent may be configured so that it will connect to the Qpid broker using SSL by
   following the steps defined in the :ref:`Qpid SSL Configuration Guide <qpid-ssl-configuration>`.
   By default, the agent will connect using a plain TCP connection.


4. Set the agent to start at boot. For upstart::

      $ sudo chkconfig goferd on
      $ sudo service goferd start

   For systemd::

      $sudo systemctl enable goferd
      $sudo systemctl start goferd


Extra Configuration
-------------------

You are now ready to proceed to :doc:`extra_configuration`.
