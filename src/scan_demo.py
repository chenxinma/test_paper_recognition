import win32com.client

# Create WIA dialog and scanner device manager
wia_dialog = win32com.client.Dispatch("WIA.CommonDialog")

# Show scanner selection dialog
device = wia_dialog.ShowSelectDevice()

if device:
    print("Selected device:", device.Properties("Name").Value)
else:
    print("No device selected")