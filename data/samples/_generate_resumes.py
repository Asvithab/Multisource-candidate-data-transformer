from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_resume(path, lines):
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 80
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
    c.save()

                                                                                            
make_resume(
    "data/samples/resume_C001.pdf",
    [
        "Asha Menon",
        "Email: asha.menon@gmail.com | Phone: +91 9876543210",
        "Bengaluru, India",
        "",
        "Backend Software Engineer at TechNova Pvt Ltd (2022 - Present)",
        "Built REST APIs serving 2M+ daily requests using Python and Django.",
        "",
        "Skills: Python, Django, PostgreSQL, Docker, AWS",
        "",
        "Education: B.E. Computer Science, Anna University, 2022",
    ],
)

                                                                                   
make_resume(
    "data/samples/resume_C004.pdf",
    [
        "Vikram Raghavan",
        "Email: vikram.raghavan@protonmail.com | Phone: 9000011122",
        "Hyderabad, India",
        "",
        "Frontend Developer at PixelWorks Labs (2023 - Present)",
        "Built responsive UIs in React and TypeScript for fintech dashboards.",
        "",
        "Skills: JavaScript, React, CSS, TypeScript",
        "",
        "Education: B.Tech Information Technology, JNTU, 2023",
    ],
)

                                                                                         
make_resume(
    "data/samples/resume_C005_garbage.pdf",
    [
        "%$#@! ---- corrupted scan artifact ----",
        "asdkj1239 !!!! ((()))",
        "",
        "no usable structured fields here",
    ],
)

print("resumes generated")