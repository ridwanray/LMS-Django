from django.db import models
from core.models import AuditableModel


class Certificate(AuditableModel):
    course = models.ForeignKey('course.Course', on_delete=models.CASCADE, related_name='certificate_generated')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='certificates')
    certificate_id =  models.CharField(max_length=20)
    grade = models.CharField(max_length=20, blank=True, null=True)
    file = models.FileField(storage='certifates/', blank=True, null=True)
    
    def __str__(self):
    	return str(self.user)