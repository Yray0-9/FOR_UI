(.venv) PS C:\Users\Public\FOR_UI> python manage.py migrate                                                                                                  
Traceback (most recent call last):
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\checks\urls.py", line 136, in check_custom_error_handlers
    handler = resolver.resolve_error_handler(status_code)
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\urls\resolvers.py", line 743, in resolve_error_handler
    callback = getattr(self.urlconf_module, "handler%s" % view_type, None)
                       ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\utils\functional.py", line 47, in __get__
    res = instance.__dict__[self.name] = self.func(instance)
                                         ~~~~~~~~~^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\urls\resolvers.py", line 722, in urlconf_module
    return import_module(self.urlconf_name)
  File "C:\Users\Admin\AppData\Local\Programs\Python\Python314\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1398, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1371, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1342, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 938, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 759, in exec_module
  File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
  File "C:\Users\Public\FOR_UI\safebooks\urls.py", line 22, in <module>
    from safebooks import views
  File "C:\Users\Public\FOR_UI\safebooks\views.py", line 83, in <module>
    from safebooks.services.admin_profile_service import (
    ...<3 lines>...
    )
  File "C:\Users\Public\FOR_UI\safebooks\services\admin_profile_service.py", line 8, in <module>
    from safebooks.services.admin_security_service import get_admin_two_factor_status
  File "C:\Users\Public\FOR_UI\safebooks\services\admin_security_service.py", line 7, in <module>
    import qrcode
ModuleNotFoundError: No module named 'qrcode'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\Public\FOR_UI\manage.py", line 22, in <module>
    main()
    ~~~~^^
  File "C:\Users\Public\FOR_UI\manage.py", line 18, in main
    execute_from_command_line(sys.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\management\__init__.py", line 443, in execute_from_command_line
    utility.execute()
    ~~~~~~~~~~~~~~~^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\management\__init__.py", line 437, in execute
    self.fetch_command(subcommand).run_from_argv(self.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\management\base.py", line 420, in run_from_argv
    self.execute(*args, **cmd_options)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\management\base.py", line 461, in execute
    self.check(**check_kwargs)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\management\base.py", line 496, in check
    all_issues = checks.run_checks(
        app_configs=app_configs,
    ...<2 lines>...
        databases=databases,
    )
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\checks\registry.py", line 89, in run_checks
    new_errors = check(app_configs=app_configs, databases=databases)
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\core\checks\urls.py", line 138, in check_custom_error_handlers
    path = getattr(resolver.urlconf_module, "handler%s" % status_code)
                   ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\utils\functional.py", line 47, in __get__
    res = instance.__dict__[self.name] = self.func(instance)
                                         ~~~~~~~~~^^^^^^^^^^
  File "C:\Users\Public\FOR_UI\.venv\Lib\site-packages\django\urls\resolvers.py", line 722, in urlconf_module
    return import_module(self.urlconf_name)
  File "C:\Users\Admin\AppData\Local\Programs\Python\Python314\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1398, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1371, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1342, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 938, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 759, in exec_module
  File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
  File "C:\Users\Public\FOR_UI\safebooks\urls.py", line 22, in <module>
    from safebooks import views
  File "C:\Users\Public\FOR_UI\safebooks\views.py", line 83, in <module>
    from safebooks.services.admin_profile_service import (
    ...<3 lines>...
    )
  File "C:\Users\Public\FOR_UI\safebooks\services\admin_profile_service.py", line 8, in <module>
    from safebooks.services.admin_security_service import get_admin_two_factor_status
  File "C:\Users\Public\FOR_UI\safebooks\services\admin_security_service.py", line 7, in <module>
    import qrcode
ModuleNotFoundError: No module named 'qrcode'
(.venv) PS C:\Users\Public\FOR_UI> 