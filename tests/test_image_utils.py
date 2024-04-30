import unittest
from unittest.mock import patch
import image_utils

class TestImageUtils(unittest.TestCase):

    def test_image_url_to_data_url(self):
        with patch('image_utils.open', unittest.mock.mock_open(read_data=b'test_image_data'), create=True) as mock_file:
            with patch('image_utils.binary_to_data_url') as mock_binary_to_data_url:
                mock_binary_to_data_url.return_value = 'data:image/png;base64,dGVzdF9pbWFnZV9kYXRh'
                result = image_utils.image_url_to_data_url('dummy_path/image.png')
                mock_file.assert_called_once_with('dummy_path/image.png', 'rb')
                mock_binary_to_data_url.assert_called_once_with(b'test_image_data')
                self.assertEqual(result, 'data:image/png;base64,dGVzdF9pbWFnZV9kYXRh')

    def test_binary_to_data_url(self):
        binary_data = b'test_binary_data'
        expected_data_url = 'data:image/jpeg;base64,dGVzdF9iaW5hcnlfZGF0YQ=='
        result = image_utils.binary_to_data_url(binary_data, mime_type='image/jpeg')
        self.assertEqual(result, expected_data_url)

        # Test with debug mode
        with patch('image_utils.open', unittest.mock.mock_open(), create=True) as mock_file:
            image_utils.binary_to_data_url(binary_data, mime_type='image/jpeg', debug=True)
            mock_file.assert_called_once_with('image_in_base64.txt', 'w')
            mock_file().write.assert_called_once_with('dGVzdF9iaW5hcnlfZGF0YQ==')

if __name__ == '__main__':
    unittest.main()




