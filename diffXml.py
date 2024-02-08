from xmldiff import main
diff = main.diff_files("ot3.xml", "ModuleTest_settings.xml")
for a in diff:
   print(a)
