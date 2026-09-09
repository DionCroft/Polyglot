"""Professional details supplied by the project owner for public display."""

NAME = "Dr Dion Miroy Mariyanayagam"
QUALIFICATIONS = "BEng (Hons) PGCert FHEA PhD MIET CEng"
ROLE = "Senior Lecturer of Electronic and Embedded Systems"
COURSES = (
    "BEng (Hons) Computer Systems Engineering and Robotics",
    "BEng (Hons) Electronics Engineering and IoT",
    "MSc Robotics with AI",
)
SCHOOL = "School of Computing and Digital Media"
DEPARTMENT = "Department of Communications Technology and Mathematics"
UNIVERSITY = "London Metropolitan University"
EMAIL = "d.mariyanayagam@londonmet.ac.uk"
CONTACT = "\n".join(
    [
        NAME + " " + QUALIFICATIONS,
        ROLE,
        "Course Leader for " + ", ".join(COURSES[:-1]) + ", and " + COURSES[-1],
        SCHOOL + ", " + DEPARTMENT + ", " + UNIVERSITY,
        "Email: " + EMAIL,
    ]
)
