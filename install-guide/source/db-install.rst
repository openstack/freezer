.. _db-install:

Install and configure database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you install and configure the Backup/Restore service,
you must install the database.

#. To install elasticsearch on Ubuntu, complete these steps:

   * Install java prerequisites:

     .. code-block:: console

        $ sudo apt-get install -y default-jre-headless

   * Download ``elasticsearch`` version 2.3.0

     .. code-block:: console

        $ wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.3.0/elasticsearch-2.3.0.deb

   * Install ``elasticsearch``

     .. code-block:: console

        $ sudo dpkg -i elasticsearch-2.3.0.deb
        $ sudo update-rc.d elasticsearch defaults 95 10



#. To install elasticsearch on Fedora, complete these steps:

   * Install java prerequisites:

     .. code-block:: console

        $ sudo yum install -y java-1.8.0-openjdk-headless

   * Download ``elasticsearch`` version 2.3.0

     .. code-block:: console

        $ wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.3.0/elasticsearch-2.3.0.rpm

   * Install ``elasticsearch``

     .. code-block:: console

        $ sudo yum install -y elasticsearch-2.3.0.rpm



