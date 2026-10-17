"""Installer lifecycle with fake OS commands: no root, services or firewall changes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

class InstallTests(unittest.TestCase):
    def test_fresh_headless_install_and_purge(self):
        with tempfile.TemporaryDirectory(prefix='mxlink-install-') as name:
            home=Path(name); binaries=home/'bin';binaries.mkdir()
            scripts={
                'systemctl':'exit 0',
                'ip': 'case "$*" in *"route"*) echo "default via 192.0.2.1 dev test0";; *) echo "1: test0 inet 192.0.2.4/24 scope global test0";; esac',
                'curl':'case "$*" in *8767/health*) printf "MX Link OK";; esac',
                'sudo':'echo "Unexpected sudo" >&2; exit 99',
                'ufw':'exit 0',
                'kpackagetool6':'echo "Plasma dependency in headless mode" >&2; exit 98',
                'dbus-update-activation-environment':'exit 0',
            }
            # Firewall is stubbed explicitly; the installer still exercises its rule logic.
            scripts['sudo']='[ "$1" = ufw ] || exit 99; exit 0'
            for tool,body in scripts.items():
                p=binaries/tool;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o700)
            env=dict(os.environ,HOME=str(home),PATH=str(binaries)+':'+os.environ['PATH'])
            result=subprocess.run(['bash',str(ROOT/'install.sh'),'--headless','--skip-deps'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertFalse((home/'.local/share/plasma/plasmoids/org.mxlink.plasmoid').exists())
            self.assertTrue((home/'.local/bin/mxlink').is_file())
            token=home/'.config/mxlink/token'
            self.assertEqual(token.stat().st_mode&0o777,0o600)
            units=home/'.config/systemd/user'
            self.assertIn('UMask=0077',(units/'mxlink.service').read_text())
            self.assertNotIn('OnlyShowIn',(home/'.config/autostart/mxlink-session-environment.desktop').read_text())
            received=home/'Downloads/MX Link/keep.txt';received.parent.mkdir(parents=True);received.write_text('keep')
            subprocess.check_call(['bash',str(ROOT/'uninstall.sh'),'--purge'],env=env,stdout=subprocess.DEVNULL)
            self.assertFalse(token.exists());self.assertFalse((home/'.local/bin/mxlink').exists())
            self.assertTrue(received.exists())
