from distutils.core import setup

setup(name='PySatel',
    version='0.1',
    description='A Python framework for automated processing of space satellite scientific data',
    author='David Parunakian',
    author_email='dp@xientific.info',
    url='http://pysatel.googlecode.com',
    py_modules=['pysatel.coord',  'pysatel.ftpfetcher', 'pysatel.hdfdriver', 'pysatel.sqldriver',  'pysatel.util'],
    scripts=['pysatel_admin.py', 'pysatel_process.py'],
    data_files=[('/etc/', ['pysatel.conf'])],
    packages=['pysatel', 'pysatel.telemetry'])
