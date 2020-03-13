from django.db import models

class Terme (models.Model):
	terme = models.CharField(primary_key=True, max_length = 100)

	def __str__(self):
		return self.terme


class Relation(models.Model):
	terme1 = models.ForeignKey(Terme, related_name='terme1', on_delete = models.CASCADE)
	relation = models.CharField( max_length = 100)
	terme2 = models.ForeignKey(Terme, related_name='terme2', on_delete = models.CASCADE)
	poids = models.IntegerField()

	class Meta:
		unique_together = (('terme1', 'relation', 'terme2'),)
		