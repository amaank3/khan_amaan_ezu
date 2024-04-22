from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from courseinfo.models import (Instructor, Section, Registration, Student, Semester, Course)
from courseinfo.forms import InstructorForm, SectionForm, CourseForm, StudentForm, RegistrationForm, SemesterForm
from courseinfo.utils import PageLinksMixin


# Create your views here.

class InstructorList(LoginRequiredMixin, PermissionRequiredMixin, PageLinksMixin, ListView):
    paginate_by = 25
    model = Instructor
    permission_required = 'courseinfo.view_instructor'

class InstructorDetail(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Instructor
    permission_required = 'courseinfo.view_instructor'
    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        instructor = self.get_object()
        section_list = instructor.sections.all()
        context["section_list"] = section_list
        return context


class InstructorCreate(LoginRequiredMixin, PermissionRequiredMixin,CreateView):
    form_class = InstructorForm
    model = Instructor
    permission_required = 'courseinfo.add_instructor'


class InstructorUpdate(LoginRequiredMixin, PermissionRequiredMixin,UpdateView):
    form_class = InstructorForm
    model = Instructor
    template_name = 'courseinfo/instructor_form_update.html'
    permission_required = 'courseinfo.change_instructor'


class InstructorDelete(LoginRequiredMixin, PermissionRequiredMixin,DeleteView):
    model = Instructor
    permission_required = 'courseinfo.delete_instructor'
    success_url = reverse_lazy('courseinfo_registration_list_urlpattern')
    def get(self, request, pk):
        instructor = get_object_or_404(Instructor,pk=pk)
        sections = instructor.sections.all()
        if sections.count() > 0:
            return render(
                request,
                'courseinfo/instructor_refuse_delete.html',
                {'instructor': instructor,
                 'sections': sections,
                 }
            )
        else:
            return render(
                request,
                'courseinfo/instructor_confirm_delete.html',
                {'instructor': instructor}
            )





class SectionList(LoginRequiredMixin, PermissionRequiredMixin,ListView):
    model = Section
    permission_required = 'courseinfo.view_section'

class SectionDetail(LoginRequiredMixin, PermissionRequiredMixin,DetailView):
    model = Section
    permission_required = 'courseinfo.view_section'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.get_object()
        context['section'] = section
        context['semester'] = section.semester
        context['course'] = section.course
        context['instructor'] = section.instructor
        context['registration_list'] = section.registrations.all()
        return context



class SectionCreate(LoginRequiredMixin, PermissionRequiredMixin,CreateView):
    form_class = SectionForm
    model = Section
    permission_required = 'courseinfo.add_section'

class SectionUpdate(LoginRequiredMixin, PermissionRequiredMixin,UpdateView):
    form_class = SectionForm
    model = Section
    template_name = 'courseinfo/section_form_update.html'
    permission_required = 'courseinfo.change_section'


class SectionDelete(LoginRequiredMixin, PermissionRequiredMixin,DeleteView):
    model = Section
    success_url = reverse_lazy('courseinfo_section_list_urlpattern')
    permission_required = 'courseinfo.delete_section'
    def get(self, request, pk):
        section = get_object_or_404(Section, pk=pk)
        registrations = section.registrations.all()
        if registrations.count() > 0:
            return render(
                request,
                'courseinfo/section_refuse_delete.html',
                {'section': section, 'registrations': registrations}
            )
        else:
            return render(
                request,
                'courseinfo/section_confirm_delete.html',
                {'section': section}
            )



class RegistrationList(LoginRequiredMixin, PermissionRequiredMixin,ListView):
    model = Registration
    permission_required = 'courseinfo.view_registration'

class RegistrationDetail(LoginRequiredMixin, PermissionRequiredMixin,DetailView):
    model = Registration
    permission_required = 'courseinfo.view_registration'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registration = self.get_object()
        context['student'] = registration.student
        context['section'] = registration.section
        return context


class RegistrationCreate(LoginRequiredMixin, PermissionRequiredMixin,CreateView):
    form_class = RegistrationForm
    model = Registration
    permission_required = 'courseinfo.add_registration'

class RegistrationUpdate(LoginRequiredMixin, PermissionRequiredMixin,UpdateView):
    form_class = RegistrationForm
    model = Registration
    template_name = 'courseinfo/registration_form_update.html'
    permission_required = 'courseinfo.change_registration'

class RegistrationDelete(LoginRequiredMixin, PermissionRequiredMixin,DeleteView):
    model = Registration
    success_url = reverse_lazy('courseinfo_registration_list_urlpattern')
    permission_required = 'courseinfo.delete_registration'

class StudentList(LoginRequiredMixin, PermissionRequiredMixin,PageLinksMixin, ListView):
    paginate_by = 25
    model = Student
    permission_required = 'courseinfo.view_student'

class StudentDetail(LoginRequiredMixin, PermissionRequiredMixin,DetailView):
    model = Student
    permission_required = 'courseinfo.view_student'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        registration_list = student.registrations.all()
        context["registration_list"] = registration_list
        return context


class StudentCreate(LoginRequiredMixin, PermissionRequiredMixin,CreateView):
    form_class = StudentForm
    model = Student
    permission_required = 'courseinfo.add_student'

class StudentUpdate(LoginRequiredMixin, PermissionRequiredMixin,UpdateView):
    form_class = StudentForm
    model = Student
    permission_required = 'courseinfo.change_student'
    template_name = 'courseinfo/student_form_update.html'

class StudentDelete(LoginRequiredMixin, PermissionRequiredMixin,DeleteView):
    model = Student
    permission_required = 'courseinfo.delete_student'
    success_url = reverse_lazy('courseinfo_student_list_urlpattern')
    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        registrations = student.registrations.all()
        if registrations.count() > 0:
            return render(
                request,
                'courseinfo/student_refuse_delete.html',
                {'student': student, 'registrations': registrations}
            )
        else:
            return render(
                request,
                'courseinfo/student_confirm_delete.html',
                {'student': student}
            )



class SemesterList(LoginRequiredMixin, PermissionRequiredMixin,ListView):
    model = Semester
    permission_required = 'courseinfo.view_semester'

class SemesterDetail(LoginRequiredMixin, PermissionRequiredMixin,DetailView):
    model = Semester
    permission_required = 'courseinfo.view_semester'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        semester = self.get_object()
        section_list = semester.sections.all()
        context["section_list"] = section_list
        return context


class SemesterCreate(LoginRequiredMixin, PermissionRequiredMixin,CreateView):
    form_class = SemesterForm
    model = Semester
    permission_required = 'courseinfo.add_semester'

class SemesterUpdate(LoginRequiredMixin, PermissionRequiredMixin,UpdateView):
    form_class = SemesterForm
    model = Semester
    permission_required = 'courseinfo.change_semester'
    template_name = 'courseinfo/semester_form_update.html'

class SemesterDelete(LoginRequiredMixin, PermissionRequiredMixin,DeleteView):
    model = Semester
    permission_required = 'courseinfo.delete_semester'
    success_url = reverse_lazy('courseinfo_semester_list_urlpattern')
    def get(self, request, pk):
        semester = get_object_or_404(Semester, pk=pk)
        sections = semester.sections.all()
        if sections.count() > 0:
            return render(
                request,
                'courseinfo/semester_refuse_delete.html',
                {'semester': semester, 'sections': sections}
            )
        else:
            return render(
                request,
                'courseinfo/semester_confirm_delete.html',
                {'semester': semester}
            )


class CourseList(LoginRequiredMixin, PermissionRequiredMixin,ListView):
    model = Course
    permission_required = 'courseinfo.view_course'

class CourseDetail(LoginRequiredMixin, PermissionRequiredMixin,DetailView):
    model = Course
    permission_required = 'courseinfo.view_course'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        section_list = course.sections.all()
        context["section_list"] = section_list
        return context


class CourseCreate(LoginRequiredMixin, PermissionRequiredMixin,CreateView):
    form_class = CourseForm
    model = Course
    permission_required = 'courseinfo.add_course'

class CourseUpdate(LoginRequiredMixin, PermissionRequiredMixin,UpdateView):
    form_class = CourseForm
    model = Course
    template_name = 'courseinfo/course_form_update.html'
    permission_required = 'courseinfo.change_course'

class CourseDelete(LoginRequiredMixin, PermissionRequiredMixin,DeleteView):
    model = Course
    permission_required = 'courseinfo.delete_course'
    success_url = reverse_lazy('courseinfo_course_list_urlpattern')
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        sections = course.sections.all()
        if sections.count() > 0:
            return render(
                request,
                'courseinfo/course_refuse_delete.html',
                {'course': course, 'sections': sections}
            )
        else:
            return render(
                request,
                'courseinfo/course_confirm_delete.html',
                {'course': course}
            )

