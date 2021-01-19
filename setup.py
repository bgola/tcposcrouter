from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='tcposcrouter',
      version='0.2.0',
      author='Bruno Gola',
      author_email='me@bgo.la',
      description='OpenSoundControl message router over TCP',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/bgola/tcposcrouter",
      packages=find_namespace_packages(include=['tcposcrouter', 'tcposcrouter.*']),
	  classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Operating System :: OS Independent",
		  "Framework :: AsyncIO",
      ],
	  install_requires=['python-osc', 'sliplib'],
      keywords='osc opensoundcontrol tcp',
      python_requires='>=3.7',
      entry_points={
          'console_scripts': [
              'tcposcrouter = tcposcrouter.__main__:main'
          ]
      },
      )
