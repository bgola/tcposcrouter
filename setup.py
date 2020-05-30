from setuptools import setup, find_namespace_packages

setup(name='tcposcrouter',
      version='0.1.0',
      packages=find_namespace_packages(include=['tcposcrouter']),
      entry_points={
          'console_scripts': [
              'tcposcrouter = tcposcrouter.__main__:main'
          ]
      },
      )
