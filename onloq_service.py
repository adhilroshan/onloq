import win32serviceutil
import win32service
import win32event
import servicemanager
import os
import sys
import subprocess

class OnloqService(win32serviceutil.ServiceFramework):
    _svc_name_ = "OnloqService"
    _svc_display_name_ = "Onloq Logger Service"
    _svc_description_ = "Service to run Onloq Logger as a background service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()

    def main(self):
        executable = sys.executable
        script_path = os.path.join(os.path.dirname(__file__), "main.py")
        self.process = subprocess.Popen([executable, script_path, "run", "--daemon"], shell=False)
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(OnloqService)

