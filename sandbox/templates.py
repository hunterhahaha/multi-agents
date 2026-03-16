from e2b import Template

template = (
    Template()
    .from_python_image('3.11')
    .pip_install
)