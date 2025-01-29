""" Setup file """
from setuptools import setup
from setuptools import find_packages
from glob import glob
from os.path import splitext
from os.path import basename
import versioneer

setup(
    name = 'vedp-conciliacion-entrecuentas-p2p',
    description = 'Es una herramienta que genera los cruces para la concilacin y compesacin del proceso de transaccin con llaves esto para el tema de entrecuentas y p2p',
    url = 'https://GrupoBancolombia@dev.azure.com/GrupoBancolombia/Vicepresidencia%20de%20Innovaci%C3%B3n%20y%20Transformaci%C3%B3n%20Digital/_git/vedp-conciliacion-entrecuentas-p2p',
    author = 'brbedoy, mamonsal',
    author_email = 'brbedoy@bancolombia.com.co',
    license = '...',
    packages = find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    python_requires='>=3.9.12',
    entry_points = {
        'console_scripts': ['vedp_conciliacion_entrecuentas_p2p = vedp_conciliacion_entrecuentas_p2p.ejecucion:main']
    },
    install_requires = [
        'future_fstrings',
        'orquestador2>=1.3.2'
    ],
    include_package_data = True,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
