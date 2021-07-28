import setuptools

setuptools.setup(
    name="resilient_async_cts",
    version="0.0.1",
    author="Liam Mahoney",
    author_email="liammahoney96@gmail.com",
    description="A library for creating asynchronous Custom Threat Services for use with the IBM Resilient SOAR platform",
    long_description="A library for creating and running an asyncrhonous Custom Threat Service that enriches artifacts for the IBM Resilient SOAR platform.",
    url="https://github.com/LiamMahoney/resilient_async_cts",
    packages=setuptools.find_packages(),
    install_requires=[
        "motor"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['resilient_async_cts=resilient_async_cts.codegen.codegen:main']
    }
)