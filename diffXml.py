from xmldiff import main
diff = main.diff_files("PS_Module_v2p1.xml", "ModuleTest_settings.xml")
for a in diff:
   print(a)
