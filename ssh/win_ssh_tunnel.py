""" Windows SSH Tunnel service
    A windows service that leverages the putty ssh tools to create and maintain a persisten ssh tunnel.
    Setup:
        Using the putty tools setup a saved session to the target host machine using an ssh key.
        Run this command in an admin shell with the arguments to install '--startup auto install'
        Ideally you should configure the service to run as a low privilege user, however
        the user will need the putty session info which is difficult to copy.
    Requires:
        pywin32 libraries.
        plink and other putty tools
"""

#I would prefer to set these on install but the pywin32 documentation is nearly non-existent
#so to save time they are here.
PUTTY_DIR = r'c:\Program Files\putty'
SESSION_NAME = 'replication'

import os
from subprocess import Popen

import servicemanager
import win32serviceutil
import win32service
import win32event


class SSHTunnelSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "SSHTunnelSvc"
    _svc_display_name_ = "SSH Tunnel"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop = win32event.CreateEvent(None, 0, 0, None)

    def _start_tunnel(self):
        return Popen([os.path.join(PUTTY_DIR, 'plink.exe'), '-batch', SESSION_NAME])
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        servicemanager.LogInfoMsg("Starting SSH Tunnel Service")
        plink = self._start_tunnel()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        while True:
            signal = win32event.WaitForSingleObject(self.stop, 3000)
            if signal == win32event.WAIT_OBJECT_0: #received stop signal
                servicemanager.LogInfoMsg("Stopping SSH Tunnel Service")
                if plink.returncode is None:
                    plink.terminate()
                self.ReportServiceStatus(win32service.SERVICE_STOPPED)
                return
            plink.poll()
            if plink.returncode is not None:
                servicemanager.LogWarningMsg("SSH Tunnel failed with plink returncode " + str(plink.returncode))
                plink = self._start_tunnel()


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(SSHTunnelSvc)
