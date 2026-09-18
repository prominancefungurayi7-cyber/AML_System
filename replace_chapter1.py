import shutil
import os

original_path = r'C:\Users\PROMINENT\Desktop\important\My Projects\Last update for AML system\AML System\Chapter 1 dissertation finale.docx'
temp_path = r'C:\Users\PROMINENT\Desktop\important\My Projects\Last update for AML system\AML System\Chapter 1 dissertation finale_temp.docx'

try:
    if os.path.exists(temp_path):
        if os.path.exists(original_path):
            os.remove(original_path)
        shutil.move(temp_path, original_path)
        print('SUCCESS: Chapter 1 file replaced successfully')
        print('Limitations and Delimitations are now in numbered point form')
except PermissionError:
    print('ERROR: File is still open in Word')
    print('ACTION REQUIRED: Close the Word file and run this script again')
    print('Temporary file location:', temp_path)
except Exception as e:
    print('ERROR:', e)
    print('Temporary file location:', temp_path)
