import os

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.storage import staticfiles_storage
from django.shortcuts import get_object_or_404
from django.test import TestCase

from courseinfo.models import Period, Year, Semester, Course, Instructor, Student, Section, Registration
from django.db import IntegrityError
from django.urls import reverse


# NOTE: Template Tests all required the additional 'name=' param in urls.py configuration for reverse() to work
# Credit to https://stackoverflow.com/questions/29590623/testing-for-links-in-a-page-content-in-django, Week 10 Tests

# Function to delete all the existing objects from migration 0005, so we can test CRUD from scratch
def clear_migration_data():
    Instructor.objects.all().delete()
    Student.objects.all().delete()


class ModelTests(TestCase):
    # Initialize to avoid "unresolved attribute reference" error
    year, period, semester, course, instructor, student, section = None, None, None, None, None, None, None

    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    @classmethod
    def setUpTestData(cls):
        cls.period = Period.objects.create(period_sequence=1, period_name="Spring")
        cls.year = Year.objects.create(year=2024)
        cls.semester = Semester.objects.create(year=cls.year, period=cls.period)
        cls.course = Course.objects.create(course_number="IS439",
                                           course_name="Web Development Using Application Frameworks")
        cls.instructor = Instructor.objects.create(first_name="Henry", last_name="Gerard", disambiguator="Harvard")
        cls.instructor_no_disambiguator = Instructor.objects.create(first_name="Mike", last_name="Ross")
        cls.student = Student.objects.create(first_name="Harvey", last_name="Specter", disambiguator="New York")
        cls.student_no_disambiguator = Student.objects.create(first_name="Jessica", last_name="Pearson")
        cls.section = Section.objects.create(section_name="AOG/AOU", semester=cls.semester,
                                             course=cls.course, instructor=cls.instructor)
        cls.registration = Registration.objects.create(student=cls.student, section=cls.section)

    def test_period(self):
        self.assertEqual(self.period.period_sequence, 1)
        self.assertEqual(self.period.period_name, "Spring")
        self.assertEqual(self.period.__str__(), "Spring")
        ordering = self.period._meta.ordering
        self.assertEqual(ordering, ["period_sequence"])

    def test_year(self):
        self.assertEqual(self.year.year, 2024)
        self.assertEqual(self.year.__str__(), "2024")
        ordering = self.year._meta.ordering
        self.assertEqual(ordering, ["year"])

    def test_semester(self):
        self.assertEqual(self.semester.year.year, 2024)
        self.assertEqual(self.semester.period.period_name, "Spring")
        self.assertEqual(self.semester.__str__(), "2024 - Spring")
        ordering = self.semester._meta.ordering
        self.assertEqual(ordering, ['year__year', 'period__period_sequence'])
        # Uniqueness constraint, can't have two of same Year/Period
        with self.assertRaises(IntegrityError):
            Semester.objects.create(year=self.year, period=self.period)
        # Incorrectly populating FK will produce ValueError
        with self.assertRaises(ValueError):
            Semester.objects.create(year="2024", period=self.period)
        with self.assertRaises(ValueError):
            Semester.objects.create(year=self.year, period="Fall")

    def test_course(self):
        self.assertEqual(self.course.course_number, "IS439")
        self.assertEqual(self.course.course_name, "Web Development Using Application Frameworks")
        self.assertEqual(self.course.__str__(), "IS439 - Web Development Using Application Frameworks")
        ordering = self.course._meta.ordering
        self.assertEqual(ordering, ["course_number", "course_name"])
        # Uniqueness constraint test
        with self.assertRaises(IntegrityError):
            Course.objects.create(course_number="IS439", course_name="Web Development Using Application Frameworks")

    def test_instructor(self):
        self.assertEqual(self.instructor.first_name, "Henry")
        self.assertEqual(self.instructor.last_name, "Gerard")
        self.assertEqual(self.instructor.disambiguator, "Harvard")
        self.assertEqual(self.instructor.__str__(), "Gerard, Henry (Harvard)")
        self.assertEqual(self.instructor_no_disambiguator.first_name, "Mike")
        self.assertEqual(self.instructor_no_disambiguator.last_name, "Ross")
        self.assertEqual(self.instructor_no_disambiguator.__str__(), "Ross, Mike")
        ordering = self.instructor._meta.ordering
        self.assertEqual(ordering, ['last_name', 'first_name', 'disambiguator'])
        # Uniqueness constraint test (error when all same, including disambiguator)
        with self.assertRaises(IntegrityError):
            Instructor.objects.create(first_name="Henry", last_name="Gerard", disambiguator="Harvard")

    def test_student(self):
        self.assertEqual(self.student.first_name, "Harvey")
        self.assertEqual(self.student.last_name, "Specter")
        self.assertEqual(self.student.disambiguator, "New York")
        self.assertEqual(self.student.__str__(), "Specter, Harvey (New York)")
        self.assertEqual(self.student_no_disambiguator.first_name, "Jessica")
        self.assertEqual(self.student_no_disambiguator.last_name, "Pearson")
        self.assertEqual(self.student_no_disambiguator.__str__(), "Pearson, Jessica")
        ordering = self.student._meta.ordering
        self.assertEqual(ordering, ['last_name', 'first_name', 'disambiguator'])
        # Uniqueness constraint test (error when all same, including disambiguator)
        with self.assertRaises(IntegrityError):
            Student.objects.create(first_name="Harvey", last_name="Specter", disambiguator="New York")

    def test_section(self):
        self.assertEqual(self.section.section_name, "AOG/AOU")
        self.assertEqual(self.section.semester.__str__(), "2024 - Spring")
        self.assertEqual(self.section.course.__str__(), "IS439 - Web Development Using Application Frameworks")
        self.assertEqual(self.section.instructor.__str__(), "Gerard, Henry (Harvard)")
        self.assertEqual(self.section.__str__(), "IS439 - AOG/AOU (2024 - Spring)")
        ordering = self.section._meta.ordering
        self.assertEqual(ordering, ['course', 'section_name', 'semester'])
        # Uniqueness constraint test
        with self.assertRaises(IntegrityError):
            Section.objects.create(section_name="AOG/AOU", semester=self.semester,
                                   course=self.course, instructor=self.instructor)

    def test_registration(self):
        self.assertEqual(self.registration.student.__str__(), "Specter, Harvey (New York)")
        self.assertEqual(self.registration.section.__str__(), "IS439 - AOG/AOU (2024 - Spring)")
        self.assertEqual(self.registration.__str__(), "IS439 - AOG/AOU (2024 - Spring) / Specter, Harvey (New York)")
        ordering = self.registration._meta.ordering
        self.assertEqual(ordering, ['section', 'student'])
        # Uniqueness constraint test
        with self.assertRaises(IntegrityError):
            Registration.objects.create(student=self.student, section=self.section)


class EmptyTemplateTests(TestCase):
    # Test response with no registrations
    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    @classmethod
    def setUpTestData(cls):
        clear_migration_data()

    def test_registration_list_view_empty(self):
        response = self.client.get(reverse('courseinfo_registration_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/registration_list.html')
        self.assertContains(response, "There are currently no registrations available.")

    # Test response with no sections
    def test_section_list_view_empty(self):
        response = self.client.get(reverse('courseinfo_section_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/section_list.html')
        self.assertContains(response, "There are currently no sections available.")

    # Test response with no instructors
    def test_instructor_list_view_empty(self):
        response = self.client.get(reverse('courseinfo_instructor_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/instructor_list.html')
        self.assertContains(response, "There are currently no instructors available.")

    # Test response with no students
    def test_student_list_view_empty(self):
        response = self.client.get(reverse('courseinfo_student_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/student_list.html')
        self.assertContains(response, "There are currently no students available.")

    # Test response with no semester
    def test_semester_list_view_empty(self):
        response = self.client.get(reverse('courseinfo_semester_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/semester_list.html')
        self.assertContains(response, "There are currently no semesters available.")

    # Test response with no courses
    def test_course_list_view_empty(self):
        response = self.client.get(reverse('courseinfo_course_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courseinfo/course_list.html")
        self.assertContains(response, "There are currently no courses available.")


# PopulatedTemplateTests have been updated for Week 10 Submission (testing Linked Pages)
class PopulatedTemplateTests(TestCase):
    # Initialize to avoid "unresolved attribute reference" error
    year, period, semester, course, instructor, student, section = None, None, None, None, None, None, None

    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    # Populate our database for these template tests
    @classmethod
    def setUpTestData(cls):
        clear_migration_data()
        cls.instructor = Instructor.objects.create(first_name="Henry", last_name="Gerard", disambiguator="Harvard")
        cls.student = Student.objects.create(first_name="Harvey", last_name="Specter", disambiguator="New York")
        cls.year = Year.objects.create(year=2024)
        cls.period = Period.objects.create(period_sequence=1, period_name="Spring")
        cls.semester = Semester.objects.create(year=cls.year, period=cls.period)
        cls.course = Course.objects.create(course_number="IS439",
                                           course_name="Web Development Using Application Frameworks")
        cls.section = Section.objects.create(section_name="AOG/AOU",
                                             semester=cls.semester,
                                             course=cls.course,
                                             instructor=cls.instructor)
        cls.registration = Registration.objects.create(student=cls.student,
                                                       section=cls.section)

    # Test response that has an instructor
    def test_instructor_list_view_populated(self):
        response = self.client.get(reverse('courseinfo_instructor_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/instructor_list.html')
        self.assertContains(response, 'Gerard, Henry (Harvard)')
        self.assertNotContains(response, "There are currently no instructors available.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.instructor.__str__()}</a>'
                            % reverse('courseinfo_instructor_detail_urlpattern',
                                      kwargs={'pk': self.instructor.pk}), html=True)

    # Test response that has a student
    def test_student_list_view_populated(self):
        response = self.client.get(reverse('courseinfo_student_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/student_list.html')
        self.assertContains(response, "Specter, Harvey (New York)")
        self.assertNotContains(response, "There are currently no students available.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.student.__str__()}</a>'
                            % reverse('courseinfo_student_detail_urlpattern',
                                      kwargs={'pk': self.student.pk}), html=True)

    # Test response with a semester
    def test_semester_list_view_populated(self):
        response = self.client.get(reverse('courseinfo_semester_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/semester_list.html')
        self.assertContains(response, "2024 - Spring")
        self.assertNotContains(response, "There are currently no semesters available.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.semester.__str__()}</a>'
                            % reverse('courseinfo_semester_detail_urlpattern',
                                      kwargs={'pk': self.semester.pk}), html=True)

    # Test response with a course
    def test_course_list_view_populated(self):
        response = self.client.get(reverse('courseinfo_course_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/course_list.html')
        self.assertContains(response, "IS439 - Web Development Using Application Frameworks")
        self.assertNotContains(response, "There are currently no courses available.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.course.__str__()}</a>'
                            % reverse('courseinfo_course_detail_urlpattern',
                                      kwargs={'pk': self.course.pk}), html=True)

    # Test response that has a section
    def test_section_list_view_populated(self):
        response = self.client.get(reverse('courseinfo_section_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courseinfo/section_list.html")
        self.assertContains(response, "IS439 - AOG/AOU (2024 - Spring)")
        self.assertNotContains(response, "There are currently no sections available.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.section.__str__()}</a>'
                            % reverse('courseinfo_section_detail_urlpattern',
                                      kwargs={'pk': self.section.pk}), html=True)

    # Test response with a registration
    def test_registration_list_view_populated(self):
        response = self.client.get(reverse('courseinfo_registration_list_urlpattern'), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/registration_list.html')
        self.assertContains(response, "IS439 - AOG/AOU (2024 - Spring) / Specter, Harvey (New York)")
        self.assertNotContains(response, "There are currently no registrations available.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.registration.__str__()}</a>'
                            % reverse('courseinfo_registration_detail_urlpattern',
                                      kwargs={'pk': self.registration.pk}), html=True)


# DetailedTemplateTests have been updated for Week 10 Submission (testing Linked Pages)
class DetailedTemplatedTests(TestCase):
    # Test Cases after Week 7, submit for Week 8 Assignment
    # Initialize to avoid "unresolved attribute reference" error
    (year, period, semester, course, instructor, student, section,
     current_year, next_year) = None, None, None, None, None, None, None, None, None

    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    @classmethod
    # Modified version of prior test data setup to include object_no_object to test multiple scenarios of HTML templates
    def setUpTestData(cls):
        cls.instructor = Instructor.objects.create(first_name="Henry", last_name="Gerard", disambiguator="Harvard")
        cls.instructor_no_section = Instructor.objects.create(first_name="Ms", last_name="Puff")  # New for W7
        cls.student = Student.objects.create(first_name="Harvey", last_name="Specter", disambiguator="New York")
        cls.student_no_registration = Student.objects.create(first_name="Louis", last_name="Litt")  # New for W7
        cls.current_year = Year.objects.create(year=2024)
        cls.next_year = Year.objects.create(year=2025)
        cls.period = Period.objects.create(period_sequence=1, period_name="Spring")
        cls.semester = Semester.objects.create(year=cls.current_year, period=cls.period)
        cls.semester_no_sections = Semester.objects.create(year=cls.next_year, period=cls.period)  # New for W7
        cls.course = Course.objects.create(course_number="IS439",
                                           course_name="Web Development Using Application Frameworks")
        cls.course_no_sections = Course.objects.create(course_number="CS225",
                                                       course_name="Data Structures and Algorithms")  # New for W7
        cls.section = Section.objects.create(section_name="AOG/AOU",
                                             semester=cls.semester,
                                             course=cls.course,
                                             instructor=cls.instructor)
        cls.section_no_students = Section.objects.create(section_name="ABC",
                                                         semester=cls.semester,
                                                         course=cls.course,
                                                         instructor=cls.instructor)  # New for W7
        cls.registration = Registration.objects.create(student=cls.student,
                                                       section=cls.section)

    def test_detailed_instructor_view(self):
        response = self.client.get(reverse('courseinfo_instructor_detail_urlpattern',
                                           kwargs={'pk': self.instructor.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/instructor_detail.html')
        self.assertContains(response, f"Instructor - {self.instructor.__str__()}")
        self.assertContains(response, self.section.__str__())  # Check related section
        self.assertNotContains(response, "There are currently no sections for this instructor.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.section.__str__()}</a>'
                            % reverse('courseinfo_section_detail_urlpattern',
                                      kwargs={'pk': self.section.pk}), html=True)

    def test_detailed_instructor_view_no_section(self):
        response = self.client.get(reverse('courseinfo_instructor_detail_urlpattern',
                                           kwargs={'pk': self.instructor_no_section.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/instructor_detail.html')
        self.assertContains(response, f"Instructor - {self.instructor_no_section.__str__()}")
        self.assertContains(response, "There are currently no sections for this instructor.")

    def test_detailed_section_view(self):
        response = self.client.get(reverse('courseinfo_section_detail_urlpattern',
                                           kwargs={'pk': self.section.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/section_detail.html')
        self.assertContains(response, f"Section - {self.section.__str__()}")
        self.assertContains(response, self.student.__str__())  # Check related student
        self.assertNotContains(response, "There are currently no students registered for this section.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.course.__str__()}</a>'
                            % reverse('courseinfo_course_detail_urlpattern',
                                      kwargs={'pk': self.course.pk}), html=True)
        self.assertContains(response, f'<a href="%s">{self.semester.__str__()}</a>'
                            % reverse('courseinfo_semester_detail_urlpattern',
                                      kwargs={'pk': self.semester.pk}), html=True)
        self.assertContains(response, f'<a href="%s">{self.instructor.__str__()}</a>'
                            % reverse('courseinfo_instructor_detail_urlpattern',
                                      kwargs={'pk': self.instructor.pk}), html=True)
        self.assertContains(response, f'<a href="%s">{self.student.__str__()}</a>'
                            % reverse('courseinfo_registration_detail_urlpattern',
                                      kwargs={'pk': self.registration.pk}), html=True)  # Note the anchor is student

    def test_detailed_section_view_no_students(self):
        response = self.client.get(reverse('courseinfo_section_detail_urlpattern',
                                           kwargs={'pk': self.section_no_students.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/section_detail.html')
        self.assertContains(response, f"Section - {self.section_no_students.__str__()}")
        self.assertContains(response, "There are currently no students registered for this section.")

    def test_detailed_semester_view(self):
        response = self.client.get(reverse('courseinfo_semester_detail_urlpattern',
                                           kwargs={'pk': self.semester.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courseinfo/semester_detail.html")
        self.assertContains(response, f"Semester - {self.semester.__str__()}")
        self.assertContains(response, self.section.__str__())  # Check related section
        self.assertNotContains(response, "There are currently no sections for this semester.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.section.__str__()}</a>'
                            % reverse('courseinfo_section_detail_urlpattern',
                                      kwargs={'pk': self.section.pk}), html=True)

    def test_detailed_semester_view_no_sections(self):
        response = self.client.get(reverse('courseinfo_semester_detail_urlpattern',
                                           kwargs={'pk': self.semester_no_sections.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courseinfo/semester_detail.html")
        self.assertContains(response, f"Semester - {self.semester_no_sections.__str__()}")
        self.assertContains(response, "There are currently no sections for this semester.")

    def test_detailed_student_view(self):
        response = self.client.get(reverse('courseinfo_student_detail_urlpattern',
                                           kwargs={'pk': self.student.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courseinfo/student_detail.html")
        self.assertContains(response, f"Student - {self.student.__str__()}")
        self.assertContains(response, self.registration.__str__())  # Check related registration
        self.assertNotContains(response, "This student is not currently registered for any sections.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.registration.__str__()}</a>'
                            % reverse('courseinfo_registration_detail_urlpattern',
                                      kwargs={'pk': self.registration.pk}), html=True)  # Note the anchor is section

    def test_detailed_student_view_no_registrations(self):
        response = self.client.get(reverse('courseinfo_student_detail_urlpattern',
                                           kwargs={'pk': self.student_no_registration.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courseinfo/student_detail.html")
        self.assertContains(response, f"Student - {self.student_no_registration.__str__()}")
        self.assertContains(response, "This student is not currently registered for any sections.")

    def test_detailed_course_view(self):
        response = self.client.get(reverse('courseinfo_course_detail_urlpattern',
                                           kwargs={'pk': self.course.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/course_detail.html')
        self.assertContains(response, f"Course - {self.course.__str__()}")
        self.assertContains(response, self.section.__str__())  # Check related section
        self.assertNotContains(response, "There are currently no sections for this course.")
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.section.__str__()}</a>'
                            % reverse('courseinfo_section_detail_urlpattern',
                                      kwargs={'pk': self.section.pk}), html=True)

    def test_detailed_course_view_no_sections(self):
        response = self.client.get(reverse('courseinfo_course_detail_urlpattern',
                                           kwargs={'pk': self.course_no_sections.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/course_detail.html')
        self.assertContains(response, f"Course - {self.course_no_sections.__str__()}")
        self.assertContains(response, "There are currently no sections for this course.")

    def test_detailed_registration_view(self):
        response = self.client.get(reverse('courseinfo_registration_detail_urlpattern',
                                           kwargs={'pk': self.registration.pk}), )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/registration_detail.html')
        self.assertContains(response, f"Registration - {self.registration.__str__()}")
        # Contains information about related objects
        self.assertContains(response, self.registration.student.__str__())
        self.assertContains(response, self.registration.section.__str__())
        # Test inclusion of proper linked pages (new for Week 10 Assignment submission)
        self.assertContains(response, f'<a href="%s">{self.student.__str__()}</a>'
                            % reverse('courseinfo_student_detail_urlpattern',
                                      kwargs={'pk': self.student.pk}), html=True)
        self.assertContains(response, f'<a href="%s">{self.section.__str__()}</a>'
                            % reverse('courseinfo_section_detail_urlpattern',
                                      kwargs={'pk': self.section.pk}), html=True)


# In addition to modification of classes above, these test cases are new for Week 10 submission.
class HomePageTests(TestCase):
    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    def test_home_page_redirects(self):
        # Home page should redirect to Section List page. This is an HTTP Code 302 (Not 200).
        response = self.client.get('', )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse('about_urlpattern'))

    def test_redirected_page_contains_linked_pages(self):
        # Defining all the anchor texts and respective [template]_list names
        header_linked_pages = {
            'Instructors': 'instructor',
            'Sections': 'section',
            'Courses': 'course',
            'Semesters': 'semester',
            'Students': 'student',
            'Registrations': 'registration'
        }
        response = self.client.get('', follow=True)  # Use follow=True parameter to follow the redirection
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'courseinfo/about.html')  # Should be section list page
        for anchor, template in header_linked_pages.items():
            self.assertContains(response, f'<a href="%s">{anchor}</a>'
                                % reverse(f'courseinfo_{template}_list_urlpattern'), html=True)


# For Week 11 (testing Week 10: Forms Assignment) CRUD Behavior
class FormCRUDTests(TestCase):
    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    @classmethod
    def setUpTestData(cls):
        clear_migration_data()

    def test_instructor_crud(self):
        # [C] Begin by Creating an Instructor
        instructor_count = Instructor.objects.count()
        get_create_instructor = self.client.get(reverse("courseinfo_instructor_create_urlpattern"), )
        self.assertEqual(get_create_instructor.status_code, 200)
        self.assertTemplateUsed(get_create_instructor, 'courseinfo/instructor_form.html')
        post_create_instructor = self.client.post(reverse('courseinfo_instructor_create_urlpattern'),
                                                  data={'first_name': 'Henry', 'last_name': 'Gerard'})
        self.assertEqual(post_create_instructor.status_code, 302)
        instructor = Instructor.objects.first()
        self.assertRedirects(post_create_instructor, reverse('courseinfo_instructor_detail_urlpattern',
                                                             kwargs={'pk': instructor.pk}))
        self.assertEqual(Instructor.objects.count(), instructor_count + 1)

        # [R] Check that the created Instructor exists (list page)
        read_instructor_list = self.client.get(reverse('courseinfo_instructor_list_urlpattern'), )
        self.assertEqual(read_instructor_list.status_code, 200)
        self.assertContains(read_instructor_list, f'<a href="%s">{instructor.__str__()}</a>'
                            % reverse('courseinfo_instructor_detail_urlpattern',
                                      kwargs={'pk': instructor.pk}), html=True)

        # [U/D] Check that update and delete exists on detailed page
        read_instructor_detailed = self.client.get(reverse("courseinfo_instructor_detail_urlpattern",
                                                           kwargs={'pk': instructor.pk}), )
        self.assertEqual(read_instructor_detailed.status_code, 200)
        self.assertContains(read_instructor_detailed,
                            f'<a href="{instructor.get_update_url()}" class="button button-primary">'
                            f'Edit Instructor</a>')
        self.assertContains(read_instructor_detailed,
                            f'<a href="{instructor.get_delete_url()}" class="button button-primary">'
                            f'Delete Instructor</a>')

        # [U] Update the instructor information
        self.assertEqual(instructor.disambiguator, "")
        get_update_instructor = self.client.get(reverse("courseinfo_instructor_update_urlpattern",
                                                        kwargs={'pk': instructor.pk}), )
        self.assertEqual(get_update_instructor.status_code, 200)
        self.assertTemplateUsed(get_update_instructor, 'courseinfo/instructor_form_update.html')
        post_update_instructor = self.client.post(reverse('courseinfo_instructor_update_urlpattern',
                                                          kwargs={'pk': instructor.pk}),
                                                  data={"first_name": "Henry",
                                                        "last_name": "Gerard",
                                                        "disambiguator": "Harvard"})
        self.assertEqual(post_update_instructor.status_code, 302)
        self.assertRedirects(post_update_instructor, reverse('courseinfo_instructor_detail_urlpattern',
                                                             kwargs={'pk': instructor.pk}))
        instructor.refresh_from_db()
        self.assertEqual(instructor.disambiguator, "Harvard")

        # [C] Trying to duplicate instructor (expect error message)
        post_duplicate = self.client.post(reverse('courseinfo_instructor_create_urlpattern'),
                                          data={'first_name': 'Henry',
                                                'last_name': 'Gerard',
                                                'disambiguator': 'Harvard'})
        self.assertEqual(post_duplicate.status_code, 200)  # No redirect because it cannot be created - odd code
        self.assertTemplateUsed(post_duplicate, 'courseinfo/instructor_form.html')
        self.assertContains(post_duplicate,
                            "<li>Instructor with this Last name, First name and Disambiguator already exists.</li>",
                            html=True)

        # [D] Attempt to delete Instructor (expect refusal due to a dependent Section)
        course = Course.objects.create(course_name='A', course_number='1')
        year = Year.objects.create(year=2024)
        period = Period.objects.create(period_sequence=1, period_name="Spring")
        semester = Semester.objects.create(year=year, period=period)
        section = Section.objects.create(section_name="G", semester=semester, course=course, instructor=instructor)
        get_delete_instructor = self.client.get(reverse('courseinfo_instructor_delete_urlpattern',
                                                        kwargs={'pk': instructor.pk}), )
        self.assertEqual(get_delete_instructor.status_code, 200)
        self.assertTemplateUsed(get_delete_instructor, 'courseinfo/instructor_refuse_delete.html')

        # [D] Delete the Section, allowing for deletion of Instructor
        section.delete()
        get_delete_instructor_confirm = self.client.get(reverse('courseinfo_instructor_delete_urlpattern',
                                                                kwargs={'pk': instructor.pk}), )
        self.assertEqual(get_delete_instructor_confirm.status_code, 200)
        self.assertTemplateUsed(get_delete_instructor_confirm, 'courseinfo/instructor_confirm_delete.html')
        post_delete_instructor = self.client.post(reverse('courseinfo_instructor_delete_urlpattern',
                                                          kwargs={'pk': instructor.pk}))
        self.assertEqual(post_delete_instructor.status_code, 302)
        self.assertRedirects(post_delete_instructor, reverse('courseinfo_instructor_list_urlpattern'))
        for obj in [semester, year, period, course]:
            obj.delete()

    def test_registration_crud(self):
        # Setting up structures necessary prior to Registration creation
        instructor = Instructor.objects.create(first_name="A", last_name="B", disambiguator="C")
        student = Student.objects.create(first_name="X", last_name="Y", disambiguator="Z")
        year = Year.objects.create(year=2024)
        period = Period.objects.create(period_sequence=1, period_name="Spring")
        semester = Semester.objects.create(year=year, period=period)
        course = Course.objects.create(course_number="CS123", course_name="Computer Science")
        section = Section.objects.create(section_name="G", semester=semester, course=course, instructor=instructor)

        # [C] Begin by Creating a Registration
        registration_count = Registration.objects.count()
        get_create_registration = self.client.get(reverse("courseinfo_registration_create_urlpattern"), )
        self.assertEqual(get_create_registration.status_code, 200)
        self.assertTemplateUsed(get_create_registration, 'courseinfo/registration_form.html')
        post_create_registration = self.client.post(reverse('courseinfo_registration_create_urlpattern'),
                                                    data={'student': student.pk, 'section': section.pk})
        self.assertEqual(post_create_registration.status_code, 302)
        registration = Registration.objects.first()
        self.assertRedirects(post_create_registration, reverse('courseinfo_registration_detail_urlpattern',
                                                               kwargs={'pk': registration.pk}))
        self.assertEqual(Instructor.objects.count(), registration_count + 1)

        # [R] Check that the created Registration exists (list page)
        read_registration_list = self.client.get(reverse('courseinfo_registration_list_urlpattern'), )
        self.assertEqual(read_registration_list.status_code, 200)
        self.assertContains(read_registration_list, f'<a href="%s">{registration.__str__()}</a>'
                            % reverse('courseinfo_registration_detail_urlpattern',
                                      kwargs={'pk': registration.pk}), html=True)

        # [U/D] Check that update and delete exists on detailed page
        read_registration_detailed = self.client.get(reverse("courseinfo_registration_detail_urlpattern",
                                                             kwargs={'pk': registration.pk}), )
        self.assertEqual(read_registration_detailed.status_code, 200)
        self.assertContains(read_registration_detailed,
                            f'<a href="{registration.get_update_url()}" class="button button-primary">'
                            f'Edit Registration</a>')
        self.assertContains(read_registration_detailed,
                            f'<a href="{registration.get_delete_url()}" class="button button-primary">'
                            f'Delete Registration</a>')

        # [U] Update the Registration information with a new student
        new_student = Student.objects.create(first_name='A', last_name='B')
        self.assertEqual(registration.student.pk, student.pk)
        get_update_instructor = self.client.get(reverse("courseinfo_registration_update_urlpattern",
                                                        kwargs={'pk': registration.pk}), )
        self.assertEqual(get_update_instructor.status_code, 200)
        self.assertTemplateUsed(get_update_instructor, 'courseinfo/registration_form_update.html')
        post_update_registration = self.client.post(reverse('courseinfo_registration_update_urlpattern',
                                                            kwargs={'pk': registration.pk}),
                                                    data={"student": new_student.pk,
                                                          "section": section.pk})
        self.assertEqual(post_update_registration.status_code, 302)
        self.assertRedirects(post_update_registration, reverse('courseinfo_registration_detail_urlpattern',
                                                               kwargs={'pk': registration.pk}))
        registration.refresh_from_db()
        self.assertEqual(registration.student.pk, new_student.pk)

        # [C] Trying to duplicate registration (expect error message)
        post_duplicate = self.client.post(reverse('courseinfo_registration_create_urlpattern'),
                                          data={"student": new_student.pk,
                                                "section": section.pk})
        self.assertEqual(post_duplicate.status_code, 200)  # No redirect because it cannot be created
        self.assertTemplateUsed(post_duplicate, 'courseinfo/registration_form.html')
        self.assertContains(post_duplicate,
                            "<li>Registration with this Section and Student already exists.</li>",
                            html=True)

        # [D] Delete registration
        get_delete_registration = self.client.get(reverse('courseinfo_registration_delete_urlpattern',
                                                          kwargs={'pk': registration.pk}), )
        self.assertEqual(get_delete_registration.status_code, 200)
        self.assertTemplateUsed(get_delete_registration, 'courseinfo/registration_confirm_delete.html')
        post_delete_registration = self.client.post(reverse('courseinfo_registration_delete_urlpattern',
                                                            kwargs={'pk': registration.pk}))
        self.assertEqual(post_delete_registration.status_code, 302)
        self.assertRedirects(post_delete_registration, reverse('courseinfo_registration_list_urlpattern'))

        # Cleanup setup objects
        for obj in [section, instructor, student, semester, year, period, course, new_student]:
            obj.delete()

    def test_section_crud(self):
        # Setting up structures necessary prior to Section creation
        instructor = Instructor.objects.create(first_name="A", last_name="B", disambiguator="C")
        year = Year.objects.create(year=2024)
        period = Period.objects.create(period_sequence=1, period_name="Spring")
        semester = Semester.objects.create(year=year, period=period)
        course = Course.objects.create(course_number="CS123", course_name="Computer Science")

        # [C] Begin by Creating a Section
        section_count = Section.objects.count()
        get_create_section = self.client.get(reverse("courseinfo_section_create_urlpattern"), )
        self.assertEqual(get_create_section.status_code, 200)
        self.assertTemplateUsed(get_create_section, 'courseinfo/section_form.html')
        post_create_section = self.client.post(reverse('courseinfo_section_create_urlpattern'),
                                               data={'section_name': 'G',
                                                     'instructor': instructor.pk,
                                                     'semester': semester.pk,
                                                     'course': course.pk})
        self.assertEqual(post_create_section.status_code, 302)
        section = Section.objects.first()
        self.assertRedirects(post_create_section, reverse('courseinfo_section_detail_urlpattern',
                                                          kwargs={'pk': section.pk}))
        self.assertEqual(Section.objects.count(), section_count + 1)

        # [R] Check that the created Section exists (list page)
        read_section_list = self.client.get(reverse('courseinfo_section_list_urlpattern'), )
        self.assertEqual(read_section_list.status_code, 200)
        self.assertContains(read_section_list, f'<a href="%s">{section.__str__()}</a>'
                            % reverse('courseinfo_section_detail_urlpattern',
                                      kwargs={'pk': section.pk}), html=True)

        # [U/D] Check that update and delete exists on detailed page
        read_section_detailed = self.client.get(reverse("courseinfo_section_detail_urlpattern",
                                                        kwargs={'pk': section.pk}), )
        self.assertEqual(read_section_detailed.status_code, 200)
        self.assertContains(read_section_detailed,
                            f'<a href="{section.get_update_url()}" class="button button-primary">'
                            f'Edit Section</a>')
        self.assertContains(read_section_detailed,
                            f'<a href="{section.get_delete_url()}" class="button button-primary">'
                            f'Delete Section</a>')

        # [U] Update the Section information
        self.assertEqual(section.section_name, "G")
        get_update_section = self.client.get(reverse("courseinfo_section_update_urlpattern",
                                                     kwargs={'pk': section.pk}), )
        self.assertEqual(get_update_section.status_code, 200)
        self.assertTemplateUsed(get_update_section, 'courseinfo/section_form_update.html')
        post_update_section = self.client.post(reverse('courseinfo_section_update_urlpattern',
                                                       kwargs={'pk': section.pk}),
                                               data={'section_name': 'UG',
                                                     'instructor': instructor.pk,
                                                     'semester': semester.pk,
                                                     'course': course.pk})
        self.assertEqual(post_update_section.status_code, 302)
        self.assertRedirects(post_update_section, reverse('courseinfo_section_detail_urlpattern',
                                                          kwargs={'pk': section.pk}))
        section.refresh_from_db()
        self.assertEqual(section.section_name, "UG")

        # [C] Trying to duplicate section (expect error message)
        post_duplicate = self.client.post(reverse('courseinfo_section_create_urlpattern'),
                                          data={'section_name': 'UG',
                                                'instructor': instructor.pk,
                                                'semester': semester.pk,
                                                'course': course.pk})
        self.assertEqual(post_duplicate.status_code, 200)  # No redirect because it cannot be created
        self.assertTemplateUsed(post_duplicate, 'courseinfo/section_form.html')
        self.assertContains(post_duplicate,
                            "<li>Section with this Semester, Course and Section name already exists.</li>",
                            html=True)

        # [D] Attempt to delete Section (expect refusal due to a dependent registration)
        student = Student.objects.create(first_name="Test", last_name="Test")
        registration = Registration.objects.create(section=section, student=student)
        get_delete_section = self.client.get(reverse('courseinfo_section_delete_urlpattern',
                                                     kwargs={'pk': section.pk}), )
        self.assertEqual(get_delete_section.status_code, 200)
        self.assertTemplateUsed(get_delete_section, 'courseinfo/section_refuse_delete.html')

        # [D] Now, removing the dependencies to actually delete Section
        registration.delete()
        student.delete()
        get_delete_section_confirm = self.client.get(reverse('courseinfo_section_delete_urlpattern',
                                                             kwargs={'pk': section.pk}), )
        self.assertEqual(get_delete_section_confirm.status_code, 200)
        self.assertTemplateUsed(get_delete_section_confirm, 'courseinfo/section_confirm_delete.html')
        post_delete_section = self.client.post(reverse('courseinfo_section_delete_urlpattern',
                                                       kwargs={'pk': section.pk}))
        self.assertEqual(post_delete_section.status_code, 302)
        self.assertRedirects(post_delete_section, reverse('courseinfo_section_list_urlpattern'))

        # Cleanup setup objects
        for obj in [instructor, semester, year, period, course]:
            obj.delete()

    def test_course_crud(self):
        # [C] Begin by Creating a Course
        course_count = Course.objects.count()
        get_create_course = self.client.get(reverse("courseinfo_course_create_urlpattern"), )
        self.assertEqual(get_create_course.status_code, 200)
        self.assertTemplateUsed(get_create_course, 'courseinfo/course_form.html')
        post_create_course = self.client.post(reverse('courseinfo_course_create_urlpattern'),
                                              data={'course_number': 'CS101',
                                                    'course_name': 'Intro Comp Sci'})
        self.assertEqual(post_create_course.status_code, 302)
        course = Course.objects.first()
        self.assertRedirects(post_create_course, reverse('courseinfo_course_detail_urlpattern',
                                                         kwargs={'pk': course.pk}))
        self.assertEqual(Course.objects.count(), course_count + 1)

        # [R] Check that the created Course exists (list page)
        read_course_list = self.client.get(reverse('courseinfo_course_list_urlpattern'), )
        self.assertEqual(read_course_list.status_code, 200)
        self.assertContains(read_course_list, f'<a href="%s">{course.__str__()}</a>'
                            % reverse('courseinfo_course_detail_urlpattern',
                                      kwargs={'pk': course.pk}), html=True)

        # [U/D] Check that update and delete exists on detailed page
        read_course_detailed = self.client.get(reverse("courseinfo_course_detail_urlpattern",
                                                       kwargs={'pk': course.pk}), )
        self.assertEqual(read_course_detailed.status_code, 200)
        self.assertContains(read_course_detailed,
                            f'<a href="{course.get_update_url()}" class="button button-primary">'
                            f'Edit Course</a>')
        self.assertContains(read_course_detailed,
                            f'<a href="{course.get_delete_url()}" class="button button-primary">'
                            f'Delete Course</a>')

        # [U] Update the Course information
        self.assertEqual(course.course_name, "Intro Comp Sci")
        get_update_course = self.client.get(reverse("courseinfo_course_update_urlpattern",
                                                    kwargs={'pk': course.pk}), )
        self.assertEqual(get_update_course.status_code, 200)
        self.assertTemplateUsed(get_update_course, 'courseinfo/course_form_update.html')
        post_update_course = self.client.post(reverse('courseinfo_course_update_urlpattern',
                                                      kwargs={'pk': course.pk}),
                                              data={'course_number': 'CS101',
                                                    'course_name': 'Comp Sci Intro'})
        self.assertEqual(post_update_course.status_code, 302)
        self.assertRedirects(post_update_course, reverse('courseinfo_course_detail_urlpattern',
                                                         kwargs={'pk': course.pk}))
        course.refresh_from_db()
        self.assertEqual(course.course_name, "Comp Sci Intro")

        # [C] Trying to duplicate course (expect error message)
        post_duplicate = self.client.post(reverse('courseinfo_course_create_urlpattern'),
                                          data={'course_number': 'CS101',
                                                'course_name': 'Comp Sci Intro'})
        self.assertEqual(post_duplicate.status_code, 200)  # No redirect because it cannot be created
        self.assertTemplateUsed(post_duplicate, 'courseinfo/course_form.html')
        self.assertContains(post_duplicate,
                            "<li>Course with this Course number and Course name already exists.</li>",
                            html=True)

        # [D] Attempt to delete Course (expect refusal due to a dependent Section)
        instructor = Instructor.objects.create(first_name="A", last_name="B", disambiguator="C")
        year = Year.objects.create(year=2024)
        period = Period.objects.create(period_sequence=1, period_name="Spring")
        semester = Semester.objects.create(year=year, period=period)
        section = Section.objects.create(section_name='G', semester=semester, course=course, instructor=instructor)
        get_delete_course = self.client.get(reverse('courseinfo_course_delete_urlpattern',
                                                    kwargs={'pk': course.pk}), )
        self.assertEqual(get_delete_course.status_code, 200)
        self.assertTemplateUsed(get_delete_course, 'courseinfo/course_refuse_delete.html')

        # [D] Now, removing the dependencies to actually delete Course
        for obj in [section, instructor, semester, year, period]:
            obj.delete()
        get_delete_course_confirm = self.client.get(reverse('courseinfo_course_delete_urlpattern',
                                                            kwargs={'pk': course.pk}), )
        self.assertEqual(get_delete_course_confirm.status_code, 200)
        self.assertTemplateUsed(get_delete_course_confirm, 'courseinfo/course_confirm_delete.html')
        post_delete_course = self.client.post(reverse('courseinfo_course_delete_urlpattern',
                                                      kwargs={'pk': course.pk}))
        self.assertEqual(post_delete_course.status_code, 302)
        self.assertRedirects(post_delete_course, reverse('courseinfo_course_list_urlpattern'))

    def test_semester_crud(self):
        # Setting up structures necessary prior to Section creation
        year = Year.objects.create(year=2024)
        period = Period.objects.create(period_sequence=1, period_name="Spring")

        # [C] Begin by Creating a Semester
        semester_count = Semester.objects.count()
        get_create_semester = self.client.get(reverse("courseinfo_semester_create_urlpattern"), )
        self.assertEqual(get_create_semester.status_code, 200)
        self.assertTemplateUsed(get_create_semester, 'courseinfo/semester_form.html')
        post_create_semester = self.client.post(reverse('courseinfo_semester_create_urlpattern'),
                                                data={'year': year.pk,
                                                      'period': period.pk})
        self.assertEqual(post_create_semester.status_code, 302)
        semester = Semester.objects.first()
        self.assertRedirects(post_create_semester, reverse('courseinfo_semester_detail_urlpattern',
                                                           kwargs={'pk': semester.pk}))
        self.assertEqual(Semester.objects.count(), semester_count + 1)

        # [R] Check that the created Semester exists (list page)
        read_semester_list = self.client.get(reverse('courseinfo_semester_list_urlpattern'), )
        self.assertEqual(read_semester_list.status_code, 200)
        self.assertContains(read_semester_list, f'<a href="%s">{semester.__str__()}</a>'
                            % reverse('courseinfo_semester_detail_urlpattern',
                                      kwargs={'pk': semester.pk}), html=True)

        # [U/D] Check that update and delete exists on detailed page
        read_semester_detailed = self.client.get(reverse("courseinfo_semester_detail_urlpattern",
                                                         kwargs={'pk': semester.pk}), )
        self.assertEqual(read_semester_detailed.status_code, 200)
        self.assertContains(read_semester_detailed,
                            f'<a href="{semester.get_update_url()}" class="button button-primary">'
                            f'Edit Semester</a>')
        self.assertContains(read_semester_detailed,
                            f'<a href="{semester.get_delete_url()}" class="button button-primary">'
                            f'Delete Semester</a>')

        # [U] Update the Semester information with a new Year
        self.assertEqual(semester.year.year, 2024)
        new_year = Year.objects.create(year=2025)
        get_update_semester = self.client.get(reverse("courseinfo_semester_update_urlpattern",
                                                      kwargs={'pk': semester.pk}), )
        self.assertEqual(get_update_semester.status_code, 200)
        self.assertTemplateUsed(get_update_semester, 'courseinfo/semester_form_update.html')
        post_update_semester = self.client.post(reverse('courseinfo_semester_update_urlpattern',
                                                        kwargs={'pk': semester.pk}),
                                                data={'year': new_year.pk,
                                                      'period': period.pk})
        self.assertEqual(post_update_semester.status_code, 302)
        self.assertRedirects(post_update_semester, reverse('courseinfo_semester_detail_urlpattern',
                                                           kwargs={'pk': semester.pk}))
        semester.refresh_from_db()
        self.assertEqual(semester.year.year, 2025)

        # [C] Trying to duplicate semester (expect error message)
        post_duplicate = self.client.post(reverse('courseinfo_semester_create_urlpattern'),
                                          data={'year': new_year.pk,
                                                'period': period.pk})
        self.assertEqual(post_duplicate.status_code, 200)  # No redirect because it cannot be created
        self.assertTemplateUsed(post_duplicate, 'courseinfo/semester_form.html')
        self.assertContains(post_duplicate,
                            "<li>Semester with this Year and Period already exists.</li>",
                            html=True)

        # [D] Attempt to delete Semester (expect refusal due to a dependent Section)
        course = Course.objects.create(course_name='Test', course_number='T1')
        instructor = Instructor.objects.create(first_name="A", last_name="B")
        section = Section.objects.create(course=course, instructor=instructor, semester=semester)
        get_delete_semester = self.client.get(reverse('courseinfo_semester_delete_urlpattern',
                                                      kwargs={'pk': semester.pk}), )
        self.assertEqual(get_delete_semester.status_code, 200)
        self.assertTemplateUsed(get_delete_semester, 'courseinfo/semester_refuse_delete.html')

        # [D] Now, removing the dependencies to actually delete Semester
        section.delete()
        get_delete_semester_confirm = self.client.get(reverse('courseinfo_semester_delete_urlpattern',
                                                              kwargs={'pk': semester.pk}), )
        self.assertEqual(get_delete_semester_confirm.status_code, 200)
        self.assertTemplateUsed(get_delete_semester_confirm, 'courseinfo/semester_confirm_delete.html')
        post_delete_semester = self.client.post(reverse('courseinfo_semester_delete_urlpattern',
                                                        kwargs={'pk': semester.pk}))
        self.assertEqual(post_delete_semester.status_code, 302)
        self.assertRedirects(post_delete_semester, reverse('courseinfo_semester_list_urlpattern'))

        # Cleanup setup objects
        for obj in [course, instructor, year, new_year, period]:
            obj.delete()

    def test_student_crud(self):
        # [C] Begin by Creating a Student
        student_count = Student.objects.count()
        get_create_student = self.client.get(reverse("courseinfo_student_create_urlpattern"), )
        self.assertEqual(get_create_student.status_code, 200)
        self.assertTemplateUsed(get_create_student, 'courseinfo/student_form.html')
        post_create_student = self.client.post(reverse('courseinfo_student_create_urlpattern'),
                                               data={'first_name': 'Henry', 'last_name': 'Gerard'})
        self.assertEqual(post_create_student.status_code, 302)
        student = Student.objects.first()
        self.assertRedirects(post_create_student, reverse('courseinfo_student_detail_urlpattern',
                                                          kwargs={'pk': student.pk}))
        self.assertEqual(Student.objects.count(), student_count + 1)

        # [R] Check that the created Student exists (list page)
        read_student_list = self.client.get(reverse('courseinfo_student_list_urlpattern'), )
        self.assertEqual(read_student_list.status_code, 200)
        self.assertContains(read_student_list, f'<a href="%s">{student.__str__()}</a>'
                            % reverse('courseinfo_student_detail_urlpattern',
                                      kwargs={'pk': student.pk}), html=True)

        # [U/D] Check that update and delete exists on detailed page
        read_student_detailed = self.client.get(reverse("courseinfo_student_detail_urlpattern",
                                                        kwargs={'pk': student.pk}), )
        self.assertEqual(read_student_detailed.status_code, 200)
        self.assertContains(read_student_detailed,
                            f'<a href="{student.get_update_url()}" class="button button-primary">'
                            f'Edit Student</a>')
        self.assertContains(read_student_detailed,
                            f'<a href="{student.get_delete_url()}" class="button button-primary">'
                            f'Delete Student</a>')

        # [U] Update the student information
        self.assertEqual(student.disambiguator, "")
        get_update_student = self.client.get(reverse("courseinfo_student_update_urlpattern",
                                                     kwargs={'pk': student.pk}), )
        self.assertEqual(get_update_student.status_code, 200)
        self.assertTemplateUsed(get_update_student, 'courseinfo/student_form_update.html')
        post_update_student = self.client.post(reverse('courseinfo_student_update_urlpattern',
                                                       kwargs={'pk': student.pk}),
                                               data={"first_name": "Henry",
                                                     "last_name": "Gerard",
                                                     "disambiguator": "Harvard"})
        self.assertEqual(post_update_student.status_code, 302)
        self.assertRedirects(post_update_student, reverse('courseinfo_student_detail_urlpattern',
                                                          kwargs={'pk': student.pk}))
        student.refresh_from_db()
        self.assertEqual(student.disambiguator, "Harvard")

        # [C] Trying to duplicate student (expect error message)
        post_duplicate = self.client.post(reverse('courseinfo_student_create_urlpattern'),
                                          data={'first_name': 'Henry',
                                                'last_name': 'Gerard',
                                                'disambiguator': 'Harvard'})
        self.assertEqual(post_duplicate.status_code, 200)  # No redirect because it cannot be created - odd code
        self.assertTemplateUsed(post_duplicate, 'courseinfo/student_form.html')
        self.assertContains(post_duplicate,
                            "<li>Student with this Last name, First name and Disambiguator already exists.</li>",
                            html=True)

        # [D] Attempt to delete Student (expect refusal due to a dependent registration)
        instructor = Instructor.objects.create(first_name="A", last_name="B", disambiguator="C")
        year = Year.objects.create(year=2024)
        period = Period.objects.create(period_sequence=1, period_name="Spring")
        semester = Semester.objects.create(year=year, period=period)
        course = Course.objects.create(course_number="CS123", course_name="Computer Science")
        section = Section.objects.create(section_name="G", semester=semester, course=course, instructor=instructor)
        registration = Registration.objects.create(student=student, section=section)
        get_delete_student = self.client.get(reverse('courseinfo_student_delete_urlpattern',
                                                     kwargs={'pk': student.pk}), )
        self.assertEqual(get_delete_student.status_code, 200)
        self.assertTemplateUsed(get_delete_student, 'courseinfo/student_refuse_delete.html')

        # [D] Delete the Registration, allowing for deletion of Student
        registration.delete()
        get_delete_student_confirm = self.client.get(reverse('courseinfo_student_delete_urlpattern',
                                                             kwargs={'pk': student.pk}), )
        self.assertEqual(get_delete_student_confirm.status_code, 200)
        self.assertTemplateUsed(get_delete_student_confirm, 'courseinfo/student_confirm_delete.html')
        post_delete_student = self.client.post(reverse('courseinfo_student_delete_urlpattern',
                                                       kwargs={'pk': student.pk}))
        self.assertEqual(post_delete_student.status_code, 302)
        self.assertRedirects(post_delete_student, reverse('courseinfo_student_list_urlpattern'))

        # Cleanup
        for obj in [section, instructor, semester, year, period, course]:
            obj.delete()


# For Week 12 (testing Week 11: Pagination and Staticfiles)
class PaginationTests(TestCase):
    # NOTE: Because of migrations, there should already be a lot of Student and Instructor objects
    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    def test_student_pagination(self):
        # Need to ensure > 25 Student entries exist before grabbing paginated list.
        self.assertTrue(Student.objects.count() > 25)
        get_paginated_student_list = self.client.get(reverse("courseinfo_student_list_urlpattern"), )
        self.assertEqual(get_paginated_student_list.status_code, 200)
        self.assertContains(get_paginated_student_list, "Page 1")
        self.assertContains(get_paginated_student_list, "<li><a href=\"?page=2\">Next</a></li>", html=True)

        # Now, clear the objects and expect the pagination buttons to disappear
        Student.objects.all().delete()
        get_non_paginated_student_list = self.client.get(reverse("courseinfo_student_list_urlpattern"), )
        self.assertEqual(get_non_paginated_student_list.status_code, 200)
        self.assertNotContains(get_non_paginated_student_list, "Page 1")
        self.assertNotContains(get_non_paginated_student_list, "<li><a href=\"?page=2\">Next</a></li>", html=True)

    def test_instructor_pagination(self):
        # Need to ensure > 25 Instructor entries exist before grabbing paginated list.
        self.assertTrue(Instructor.objects.count() > 25)
        get_paginated_instructor_list = self.client.get(reverse("courseinfo_instructor_list_urlpattern"), )
        self.assertEqual(get_paginated_instructor_list.status_code, 200)
        self.assertContains(get_paginated_instructor_list, "Page 1")
        self.assertContains(get_paginated_instructor_list, "<li><a href=\"?page=2\">Next</a></li>", html=True)

        # Now, clear the objects and expect the pagination buttons to disappear
        Instructor.objects.all().delete()
        get_non_paginated_instructor_list = self.client.get(reverse("courseinfo_instructor_list_urlpattern"), )
        self.assertEqual(get_non_paginated_instructor_list.status_code, 200)
        self.assertNotContains(get_non_paginated_instructor_list, "Page 1")
        self.assertNotContains(get_non_paginated_instructor_list, "<li><a href=\"?page=2\">Next</a></li>", html=True)

    # Check that we don't paginate until the required number of objects are reached
    def test_pagination_threshold(self):
        clear_migration_data()  # Clears all Student and Instructor objects
        for i in range(25):  # We add 25 objects of each because we paginate at 25
            Instructor.objects.create(first_name=str(i), last_name=str(i))
            Student.objects.create(first_name=str(i), last_name=str(i))
        get_student_list = self.client.get(reverse("courseinfo_student_list_urlpattern"), )
        get_instructor_list = self.client.get(reverse("courseinfo_instructor_list_urlpattern"), )
        for response in [get_student_list, get_instructor_list]:
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Page 1")
            self.assertNotContains(response, "<li><a href=\"?page=2\">Next</a></li>", html=True)


# For Week 12 (testing Week 11: Pagination and Staticfiles)
class StaticFileTests(TestCase):
    # Initialize to avoid "unresolved attribute reference" error
    year, period, semester, course, instructor, student, section = None, None, None, None, None, None, None

    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')
    # Set up one of each object. This way we can test pages that require kwarg pk=n

    @classmethod
    def setUpTestData(cls):
        cls.period = Period.objects.create(period_sequence=1, period_name="Spring")
        cls.year = Year.objects.create(year=2024)
        cls.semester = Semester.objects.create(year=cls.year, period=cls.period)
        cls.course = Course.objects.create(course_number="IS439",
                                           course_name="Web Development Using Application Frameworks")
        cls.instructor = Instructor.objects.create(first_name="Henry", last_name="Gerard", disambiguator="Harvard")
        cls.instructor_no_disambiguator = Instructor.objects.create(first_name="Mike", last_name="Ross")
        cls.student = Student.objects.create(first_name="Harvey", last_name="Specter", disambiguator="New York")
        cls.student_no_disambiguator = Student.objects.create(first_name="Jessica", last_name="Pearson")
        cls.section = Section.objects.create(section_name="AOG/AOU", semester=cls.semester,
                                             course=cls.course, instructor=cls.instructor)
        cls.registration = Registration.objects.create(student=cls.student, section=cls.section)

    def test_find_static_files(self):
        normalize_path = os.path.join(settings.STATIC_ROOT, 'courseinfo', 'normalize.css')
        self.assertTrue(staticfiles_storage.exists(normalize_path))
        skeleton_path = os.path.join(settings.STATIC_ROOT, 'courseinfo', 'skeleton.css')
        self.assertTrue(staticfiles_storage.exists(skeleton_path))
        style_sheet_path = os.path.join(settings.STATIC_ROOT, 'courseinfo', 'style.css')
        self.assertTrue(staticfiles_storage.exists(style_sheet_path))

    # Can theoretically duplicate this method for any response that expects a templated page using updated CSS
    def test_home_uses_static_files(self):
        response = self.client.get('', follow=True)
        for file_name in ["normalize", "skeleton", "style"]:
            self.assertContains(response, f"{file_name}.css")

    # For now, we clone the CSS inclusion code to test GET on all List/Detail/C/U/D pages for each object

    def test_get_list_pages_use_static_files(self):
        for obj in ["instructor", "section", "course", "semester", "student", "registration"]:
            response = self.client.get(reverse(f"courseinfo_{obj}_list_urlpattern"))
            for file_name in ["normalize", "skeleton", "style"]:
                self.assertContains(response, f"{file_name}.css")

    def test_get_detail_pages_use_static_files(self):
        for obj in ["instructor", "section", "course", "semester", "student", "registration"]:
            response = self.client.get(reverse(f"courseinfo_{obj}_detail_urlpattern", kwargs={"pk": 1}))
            for file_name in ["normalize", "skeleton", "style"]:
                self.assertContains(response, f"{file_name}.css")

    def test_get_create_pages_use_static_files(self):
        for obj in ["instructor", "section", "course", "semester", "student", "registration"]:
            response = self.client.get(reverse(f"courseinfo_{obj}_create_urlpattern"))
            for file_name in ["normalize", "skeleton", "style"]:
                self.assertContains(response, f"{file_name}.css")

    def test_get_update_pages_use_static_files(self):
        for obj in ["instructor", "section", "course", "semester", "student", "registration"]:
            response = self.client.get(reverse(f"courseinfo_{obj}_update_urlpattern", kwargs={"pk": 1}))
            for file_name in ["normalize", "skeleton", "style"]:
                self.assertContains(response, f"{file_name}.css")

    def test_get_delete_pages_use_static_files(self):
        for obj in ["instructor", "section", "course", "semester", "student", "registration"]:
            response = self.client.get(reverse(f"courseinfo_{obj}_delete_urlpattern", kwargs={"pk": 1}))
            for file_name in ["normalize", "skeleton", "style"]:
                self.assertContains(response, f"{file_name}.css")


# For Week 13 (testing Week 12: Generic Class-Based Views)
class Week13Tests(TestCase):
    # This setUp method is added this week since we have authentication and auth, we need to be a superuser testing
    def setUp(self):
        User.objects.create_superuser('test', 'test@example.com', 'pass')
        self.client.login(username='test', password='pass')

    # Test the new "About" page
    def test_about_page(self):
        get_about = self.client.get(reverse('about_urlpattern'))
        self.assertEqual(get_about.status_code, 200)
        self.assertTemplateUsed(get_about, 'courseinfo/about.html')

    # Test new paginated navigation "first" and "last" buttons
    def test_new_list_page_navigation(self):
        get_student_list = self.client.get(reverse('courseinfo_student_list_urlpattern'))
        self.assertEqual(get_student_list.status_code, 200)
        self.assertContains(get_student_list, "<li><a href=\"?page=5\">Last</a></li>", html=True)
        get_student_list_second_page = self.client.get(reverse('courseinfo_student_list_urlpattern') + '?page=2')
        self.assertEqual(get_student_list_second_page.status_code, 200)
        self.assertContains(get_student_list_second_page, "<li><a href=\"?page=1\">First</a></li>", html=True)
        get_instructor_list = self.client.get(reverse('courseinfo_instructor_list_urlpattern'))
        self.assertEqual(get_instructor_list.status_code, 200)
        self.assertContains(get_instructor_list, "<li><a href=\"?page=5\">Last</a></li>", html=True)
        get_instructor_list_second_page = self.client.get(reverse('courseinfo_instructor_list_urlpattern') + '?page=2')
        self.assertEqual(get_instructor_list_second_page.status_code, 200)
        self.assertContains(get_instructor_list_second_page, "<li><a href=\"?page=1\">First</a></li>", html=True)
    # Otherwise, nothing new to test for this week because the content is the same
    # But the setUp(self) method has been added to all other test classes this week to support auth


# For Week 14 (testing Week 13: Authentication and Authorization)
class LoginLogoutBehavior(TestCase):
    def setUp(self):
        User.objects.create_user(username="test", password="secret")

    def test_login_page(self):
        get_login_page = self.client.get(reverse('login_urlpattern'))
        self.assertTemplateUsed(get_login_page, 'courseinfo/login.html')

    # we know login redirects you to "about" given the settings.py
    def test_login_functionality(self):
        response = self.client.post(reverse('login_urlpattern'),
                                    data={'username': 'test', 'password': 'secret'},
                                    follow=True)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('about_urlpattern'))

    # wek now logout redirects you to the login page
    def test_logout_functionality(self):
        self.client.login(username='test', password='secret')
        response = self.client.get(reverse('logout_urlpattern'), follow=True)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('login_urlpattern'))


# For Week 14 (testing Week 13: Authentication and Authorization)
class AuthenticationAuthorizationTests(TestCase):
    # For now, we can only test the superuser and user authentications. The latest migration does not seem to apply to
    # the testing DB for some reason. Cannot figure out.
    def setUp(self):
        User.objects.create_superuser(username='sysadmin', password='pass')
        user = User.objects.create_user(username='user', password='pass')
        user_group = Group.objects.get(name='ci_user')
        user_group.user_set.add(user)

        self.instructor = Instructor.objects.create(first_name="Henry", last_name="Gerard", disambiguator="Harvard")
        self.student = Student.objects.create(first_name="Harvey", last_name="Specter", disambiguator="New York")
        self.current_year = Year.objects.create(year=2024)
        self.period = Period.objects.create(period_sequence=1, period_name="Spring")
        self.semester = Semester.objects.create(year=self.current_year, period=self.period)
        self.course = Course.objects.create(course_number="IS439",
                                            course_name="Web Development Using Application Frameworks")
        self.section = Section.objects.create(section_name="AOG/AOU",
                                              semester=self.semester,
                                              course=self.course,
                                              instructor=self.instructor)
        self.registration = Registration.objects.create(student=self.student,
                                                        section=self.section)

    # See: https://docs.djangoproject.com/en/5.0/topics/auth/default/#permission-caching
    @staticmethod
    def refresh_user(username):
        return get_object_or_404(User, username=username)

    def test_sysadmin(self):
        sysadmin = self.refresh_user('sysadmin')
        self.client.force_login(sysadmin)
        full_permission_objects = ['semester', 'course', 'section', 'instructor', 'student', 'registration']
        for obj in full_permission_objects:
            view_response = self.client.get(reverse(f"courseinfo_{obj}_list_urlpattern"))
            create_response = self.client.get(reverse(f"courseinfo_{obj}_create_urlpattern"))
            update_response = self.client.get(reverse(f"courseinfo_{obj}_update_urlpattern", kwargs={'pk': 1}))
            delete_response = self.client.get(reverse(f"courseinfo_{obj}_delete_urlpattern", kwargs={'pk': 1}))
            self.assertEqual(view_response.status_code, 200)
            self.assertEqual(create_response.status_code, 200)
            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(delete_response.status_code, 200)

    def test_non_superuser(self):
        user = self.refresh_user('user')
        self.client.force_login(user)
        no_permission_objects = ['semester', 'course', 'section', 'instructor', 'student', 'registration']
        for obj in no_permission_objects:
            view_response = self.client.get(reverse(f"courseinfo_{obj}_list_urlpattern"))
            create_response = self.client.get(reverse(f"courseinfo_{obj}_create_urlpattern"))
            update_response = self.client.get(reverse(f"courseinfo_{obj}_update_urlpattern", kwargs={'pk': 1}))
            delete_response = self.client.get(reverse(f"courseinfo_{obj}_delete_urlpattern", kwargs={'pk': 1}))
            self.assertEqual(view_response.status_code, 403)
            self.assertEqual(create_response.status_code, 403)
            self.assertEqual(update_response.status_code, 403)
            self.assertEqual(delete_response.status_code, 403)