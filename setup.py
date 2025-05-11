import setuptools

setuptools.setup(
    name="streamlit-markmap",
    version="1.0.3",
    author="FutureCast",
    author_email="",
    description="Enhanced markmap component for Streamlit with interactive features",
    long_description="A Streamlit component that renders Markdown as interactive mind maps with pan, zoom, and toolbar features.",
    long_description_content_type="text/plain",
    url="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.8",
    install_requires=[
        "streamlit >= 0.63",
    ],
)
