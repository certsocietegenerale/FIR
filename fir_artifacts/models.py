from django.db import models

class ArtifactBlacklistItem(models.Model):
	type = models.CharField(max_length=20)
	value = models.CharField(max_length=200)

	def __unicode__(self):
		return self.value

class ArtifactWhitelistItem(models.Model):
	type = models.CharField(max_length=20)
	value = models.CharField(max_length=200)

	def __unicode__(self):
		return self.value
