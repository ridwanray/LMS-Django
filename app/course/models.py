from django.db import models
from core.models import AuditableModel
from core.fields import ArrayFileField 
from core.enums import COURSE_PAYMENT_STATUS
#from ckeditor.fields import RichTextField


class Course(AuditableModel):
    course_name= models.CharField(max_length=40)
    course_price = models.DecimalField(default=0,max_digits=20,decimal_places=2,blank=True, null=True)
    display_title=  models.CharField(max_length=60, blank=True, null=True)
    short_description = models.CharField(max_length=100, blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    video_hours = models.CharField(max_length=60, blank=True, null=True)
    teachers = models.ManyToManyField("user.User", related_name="courses_taking", blank=True)
    is_active =  models.BooleanField(default=True)
    approved = models.BooleanField(default=False) 
    created_by = models.ForeignKey("user.User", related_name="courses_created", on_delete=models.SET_NULL, blank=True, null=True)
    approved_by = models.ForeignKey("user.User", related_name="courses_approved",on_delete=models.SET_NULL, blank=True, null=True)
    
    @property
    def student_enrolled_count(self):
        return self.students_enrolled.count()
    
    @property
    def total_modules(self):
        return self.modules.count()
    
    @property
    def total_teachers(self):
        return self.teachers.count()

    def __str__(self):
    	return f'{self.course_name}'
 

class EnrollStudent(AuditableModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='enrolled_courses', )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_students')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(default=0,max_digits=20,decimal_places=2,blank=True, null=True)
    
    def __str__(self):
    	return f'{self.user} - {self.course}'

class Module(AuditableModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    module_name = models.CharField(max_length=40, blank=True, null=True)
    video_link= models.CharField(max_length=250, blank=True, null=True)
    module_order = models.PositiveIntegerField(blank=True, null=True)
    topic=models.CharField(max_length=30, blank=True, null=True)
    text_cotent= models.TextField(blank=True, null=True)
    practical_work_sheet = ArrayFileField(models.FileField(upload_to="practical_work_sheet/", null=True, blank=True), null=True)
    created_by = models.ForeignKey('user.User', on_delete=models.SET_NULL, related_name='modules_created', blank=True, null=True)
    completed_by = models.ManyToManyField("user.User", related_name="completed_modules", blank=True)
    
    class Meta:
        ordering = ('-course', 'module_order')
    
    def __str__(self):
    	return f'{self.module_name} {self.course}'

    
class ModuleAssignmentSubmission(AuditableModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='submitted_module_assignments')
    user =models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='user_module_assignments')
    assigment_file = models.FileField(upload_to="practical_work_sheet/", blank=True, null=True)

    def __str__(self):
        return f'{self.user}  {self.module}'


class Transaction(AuditableModel):
    user =  models.ForeignKey("user.User", related_name="user_transactions",  on_delete=models.SET_NULL, blank=True, null=True)
    course = models.ForeignKey(Course, related_name="transactions",  on_delete=models.SET_NULL,blank=True, null=True,)
    amount_paid = models.FloatField()
    status = models.CharField(max_length=15, choices=COURSE_PAYMENT_STATUS, blank=True, null=True)
