from setuptools import setup, find_packages

setup(
    name="cycling-route-video",
    version="1.0.0",
    description="Universal Cycling Route Video Generator",
    author="hy4015",
    packages=find_packages(),
    install_requires=[
        "pillow>=10.0.0",
        "imageio-ffmpeg>=0.4.9",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "cycling-video=engine.pipeline:main",
            "cycling-route-video=engine.pipeline:main",
        ],
    },
    python_requires=">=3.8",
)
