2. Edit the ``/etc/freezer-api/freezer-api.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://freezer-api:FREEZER-API_DBPASS@controller/freezer-api
