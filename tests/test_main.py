import os
import unittest
from unittest.mock import patch, MagicMock

from space_warner.main import get_disk_usage, parse_filesystem_setting, monitor, warn


class TestDiskUsage(unittest.TestCase):
    def test_get_disk_usage(self):
        mocked_output = 'Filesystem     Avail  Use%\n/dev/sda1       100G    90%\n/dev/sda2       200G    80%'  # noqa
        with patch('subprocess.run', return_value=MagicMock(stdout=mocked_output)):
            result = get_disk_usage()
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['filesystem'], '/dev/sda1')
            self.assertEqual(result[0]['avail'], '100G')
            self.assertEqual(result[0]['used%'], '90%')
            self.assertEqual(result[1]['filesystem'], '/dev/sda2')
            self.assertEqual(result[1]['avail'], '200G')
            self.assertEqual(result[1]['used%'], '80%')

    def test_parse_filesystem_setting(self):
        os.environ['GLOBAL_THRESHOLD'] = '0.95'
        os.environ['FILE_SYSTEMS'] = '/filesystem1::0.9,/filesystem2::0.8,/filesystem/3,/filesystem/4::0.54'  # noqa
        result = parse_filesystem_setting()
        self.assertEqual(result['/filesystem1'], 0.9)
        self.assertEqual(result['/filesystem2'], 0.8)
        self.assertEqual(result['/filesystem/3'], 0.95)
        self.assertEqual(result['/filesystem/4'], 0.54)

    def test_warn(self):
        with patch('requests.post') as mock_post:
            warn('test_fs', '50%')
            mock_post.assert_called_once_with(
                os.environ.get('API_ENDPOINT', ''),
                headers={'Content-type': 'application/json'},
                json={'text': 'WARNING: test_fs: used 50%'}
            )

    @patch.dict(os.environ, {'TRIGGER_INTERVAL': '30', 'WARNING_INTERVAL': '900'})
    @patch('time.sleep', side_effect=lambda x: None)
    @patch('space_warner.main.get_disk_usage')
    @patch('space_warner.main.parse_filesystem_setting')
    @patch('space_warner.main.warn')
    def test_monitor_warning(self, mock_warn, mock_parse, mock_disk, mock_sleep):
        mock_disk.return_value = [
            {'filesystem': '/dev/sda1', 'used%': '80%'},
            {'filesystem': '/dev/sda2', 'used%': '30%'}
        ]
        mock_parse.return_value = {
            '/dev/sda1': 70,
            '/dev/sda2': 50
        }

        monitor(mock_disk.return_value, mock_parse.return_value, 30, 900)

        mock_warn.assert_called_once_with(filesystem='/dev/sda1', used='80%')
        mock_sleep.assert_called_once_with(900)

    @patch.dict(os.environ, {'TRIGGER_INTERVAL': '30', 'WARNING_INTERVAL': '900'})
    @patch('time.sleep', side_effect=lambda x: None)
    @patch('space_warner.main.get_disk_usage')
    @patch('space_warner.main.parse_filesystem_setting')
    @patch('space_warner.main.warn')
    def test_monitor_no_warning(self, mock_warn, mock_parse, mock_disk, mock_sleep):
        mock_disk.return_value = [
            {'filesystem': '/dev/sda1', 'used%': '80%'},
            {'filesystem': '/dev/sda2', 'used%': '30%'}
        ]
        mock_parse.return_value = {
            '/dev/sda1': 90,
            '/dev/sda2': 40,
        }

        monitor(mock_disk.return_value, mock_parse.return_value, 30, 900)

        mock_warn.assert_not_called()
        mock_sleep.assert_called_once_with(30)
