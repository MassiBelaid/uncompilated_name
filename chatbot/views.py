from django.shortcuts import render
from django.http import HttpResponse
from datetime import date
from chatbot.models import Terme,Relation,RelationAVerifier
import re
import random
from django.db.models import Q
import urllib.request
from threading import Thread


NON_FORT = -10
NON_FAIBLE = -2
SAIS_PAS = 5
OUI_FAIBLE = 30
NOMBRE_VALIDATION_RELATION = 2

LIST_IS_A = ["est un", "est une sous-classe de", "est un sous-ensemble de", "appartient à la classe de"]
LIST_HAS_PART = ["est composé de", "est une partie de"]
LIST_HAS_ATTRIBUTE = ["peut être qualifié de", "peut avoir comme propriété de","a comme propriété de", "est qualifié de","peut","sait"]

LIST_OUI_FORT = ["certainement","sûrement","absolument"]
LIST_OUI_FAIBLE = ["en majorité","globalement","probablement","dans beaucoup de cas"]
LIST_SAIS_PAS = ["peut-être","Pas toujours","eventuellement","pas forcément"]
LIST_NON_FORT = ["absolument pas","impossible","pas du tout"]
LIST_NON_FAIBLE = ["plutôt pas","peut-être pas","j'en doute","je ne crois pas"]

LIST_REPONSE_OUI_FORT = ["oui certainement","oui sûrement","oui absolument","oui surement","oui"]
LIST_REPONSE_OUI_FAIBLE = ["oui en majorité","oui globalement","oui probablement","oui dans beaucoup de cas","oui en majorite"]
LIST_REPONSE_SAIS_PAS = ["peut-être","Pas toujours","eventuellement","pas forcément","pas forcement","peut-etre"]
LIST_REPONSE_NON_FORT = ["absolument pas","impossible","pas du tout","non"]
LIST_REPONSE_NON_FAIBLE = ["plutôt pas","peut-être pas","j'en doute","je ne crois pas","plutot pas","peut-etre pas"]

LIST_EVIDENT = ["parce que c'est évident", "c'est factuel","parce ce que c'est un fait","c'est évident"]

LIST_DETERMINANT = ["un","une","des","la","le","les"]

LIST_CONJ_ETRE = ["est","sont"]
LIST_CONJ_APPARTENIR = ["appartient","appartiennent"]

RAFFINEMENT = "nul0"



def home(request):
	today = date.today()
	phrase = request.GET.get('phrase') or ''
	rav = request.session.get('question')
	if (rav is not None) :
		if(phrase == '') :
			request.session['question'] = None
			return render(request,'chatbot/chatbot.html',{'date':today, 'reponse':"Bonjour, je suis Greg. Que veux-tu savoir ?"})
		else :
			reponse = traitement_reponse(rav, phrase)
			request.session['question'] = None
			if(type(reponse) == str) :
				return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse})
			else :
				request.session['question'] = reponse
				reponse = construireQuestion (reponse)
				return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse})
	else :	
		if(phrase == '') :
			return render(request,'chatbot/chatbot.html',{'date':today, 'reponse':"Bonjour, je suis Greg. Que veux-tu savoir ?"})
		else :
			reponse = traitement_phrase(phrase)
			if(type(reponse) == str) :
				return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse})
			else :
				request.session['question'] = reponse
				reponse = construireQuestion (reponse)
				return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse})




def extraire(terme) :

	r6 = extraireJDM(terme,"6")
	r9 = extraireJDM(terme,"9")
	print("======================================================================={}".format(extraireJDM(terme,"6")))
	print("======================================================================={}".format(extraireJDM(terme,"9")))
	return r6


def extraireJDM(terme, numRel) :
	termeURL = terme.replace("é","%E9").replace("è","%E8").replace("ê","%EA").replace("à","%E0").replace("ç","%E7")
	with urllib.request.urlopen("http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={}&rel={}".format(termeURL,numRel)) as url :
		s = url.read().decode('latin-1')
		if("<CODE>" in s):
			lesTermes = s[s.find("// les noeuds/termes (Entries) : e;eid;'name';type;w;'formated name'") + len("// les noeuds/termes (Entries) : e;eid;'name';type;w;'formated name'"):s.find("// les types de relations (Relation Types) : rt;rtid;'trname';'trgpname';'rthelp'")]
			lesRelSort = s[s.find("// les relations sortantes : r;rid;node1;node2;type;w") + len("// les relations sortantes : r;rid;node1;node2;type;w"):s.find("// les relations entrantes : r;rid;node1;node2;type;w ")]
			lesRelEntr = s[s.find("// les relations entrantes : r;rid;node1;node2;type;w ") + len("// les relations entrantes : r;rid;node1;node2;type;w "):s.find("// END")]
			lesTermesTab = lesTermes.split("\n")
			lesRelSorTab = lesRelSort.split("\n")
			lesRelEntrTab = lesRelEntr.split("\n")
			listTouteRelation = lesRelSorTab + lesRelEntrTab
			for ligne in lesTermesTab :
				casesTermes = ligne.split(";")
					
				if(len(casesTermes) == 6):
					if(">" in casesTermes[5] and not("=" in casesTermes[5])) :
						existTBool = False
						if(Terme.objects.filter(id = casesTermes[1]).exists()):
							existTBool = True
						if(existTBool == False)	:
							caseDuTerme = casesTermes[5]
							caseDuTerme = caseDuTerme[1: len(caseDuTerme)-1]
							if(not Terme.objects.filter(id = casesTermes[1]).exists() and len(caseDuTerme.split(">")[0]) < 100 and int(casesTermes[4]) > 50 ):
								Terme.objects.create(id = casesTermes[1], terme = caseDuTerme.split(">")[0], raffinement = caseDuTerme.split(">")[1], importe = "0")
								
				elif(len(casesTermes) == 5 and not("=" in casesTermes[2])) :
					id = casesTermes[1]
					caseDuTerme = casesTermes[2]
					caseDuTerme = caseDuTerme[1: len(caseDuTerme)-1]
					if(caseDuTerme.lower() == terme and len(caseDuTerme) < 100 and int(casesTermes[4]) > 50) :
						idDuTerme = casesTermes[1]
						Terme(id = idDuTerme, terme = caseDuTerme, raffinement = RAFFINEMENT).delete()
						Terme.objects.create(id = idDuTerme, terme = caseDuTerme, raffinement = RAFFINEMENT, importe = "1")
					else :
						if(not Terme.objects.filter(id = casesTermes[1]).exists() and len(caseDuTerme) < 100 and int(casesTermes[4]) > 50):					
							Terme.objects.create(id = casesTermes[1], terme = caseDuTerme, raffinement = RAFFINEMENT, importe = "0")
							

			for ligne in listTouteRelation :
				casesRelation = ligne.split(";")
				if(len(casesRelation) == 6):
						
					if(numRel == "1") :
						r = "raff_sem"
					elif(numRel == "6") :
						r = "is_a"
					elif(numRel == "9") :
						r = "has_part"
					existeTermBool = Terme.objects.filter(id = casesRelation[3]).exists() and Terme.objects.filter(id = casesRelation[2]).exists() and not Relation.objects.filter(terme1 = Terme.objects.get(id = casesRelation[2]), terme2 = Terme.objects.get(id = casesRelation[3]), relation = r).exists()
					if(existeTermBool):
						Relation.objects.create(relation = r, source = "JDM", poids = casesRelation[5], terme1 = Terme.objects.get(id = casesRelation[2]), terme2 = Terme.objects.get(id = casesRelation[3]) )
			return idDuTerme
		else :
			return -1

		







def view_date(request, jour, mois, annee=2020):
	return render (request,'chatbot/date.html',locals())


def toSingular(ter) :
	#A REVOIR
	motSing = Relation.objects.filter(terme1= ter, relation = "plur")
	for m in motSing :
		ter = m.terme2
	return ter




def isADeterminant(det):
	if(det in LIST_DETERMINANT) :
		return True
	else :
		return False



def separateurSymboleTerme(ter) :
	if(ter[len(ter)-1] == '?') :
		ter = ter[0:len(ter)-1]
	if(ter[0] == 'l' and ter[1] == "\'") :
		ter = ter[2:len(ter)]
	return ter



def existTerme(ter) :
    idTerme = -1
    if(Terme.objects.filter(terme = ter, raffinement = RAFFINEMENT, importe = "1").exists()) :
    	termeBDDl = Terme.objects.get(terme = ter, importe = "1", raffinement = RAFFINEMENT)
    	idTerme = termeBDDl.id
    if(idTerme == -1) :
    	idTerme = extraire(ter)

    return idTerme 




def searchRelation(termeU1,relation_recherchee,termeU2) :
	#termeU1 = toSingular(termeU1)
	#
	#A REVOIRtermeU2 = toSingular(termeU2)
	find = False
	listRelations = Relation.objects.filter(terme1 = termeU1, relation = relation_recherchee, terme2 = termeU2)
	for rel in listRelations :
		find = True
		if (rel.poids < NON_FORT):
			return random.choice(LIST_NON_FORT)
		elif(rel.poids < NON_FAIBLE):
			return random.choice(LIST_NON_FAIBLE)
		elif(rel.poids < SAIS_PAS) :
			return random.choice(LIST_SAIS_PAS)
		elif(rel.poids < OUI_FAIBLE) :
			return "{} oui.".format(random.choice(LIST_OUI_FAIBLE))
		else :
			return "{} oui.".format(random.choice(LIST_OUI_FORT))
	if(find == False) :
		listRelations = Relation.objects.filter(terme1= termeU1, relation = relation_recherchee)
		for rel in listRelations :
			p1 = rel.poids
			listRelations2 = Relation.objects.filter(terme2= termeU2, relation = relation_recherchee, terme1 = rel.terme2.id)
			for rel2 in listRelations2 :
				p2 = rel2.poids
				if(p1 >= OUI_FAIBLE and p2 >= OUI_FAIBLE) :
					reponse = "{} oui.".format(random.choice(LIST_OUI_FORT))
					find = True
				elif((p1 < OUI_FAIBLE and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < OUI_FAIBLE)) :
					if((p1 >= SAIS_PAS and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= SAIS_PAS)) :
						reponse = "{} oui.".format(random.choice(LIST_OUI_FAIBLE))
						find = True
					elif((p1 >= NON_FAIBLE and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FAIBLE)) :
						reponse = random.choice(LIST_SAIS_PAS)
						poids = 0
						find = True
					elif((p1 >= NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FORT)) :
						reponse = random.choice(LIST_NON_FAIBLE)
						find = True
					elif((p1 < NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < NON_FORT)) :
						reponse = random.choice(LIST_NON_FORT)
						find = True
					
		if(find) :
			if(RelationAVerifier.objects.filter(terme1 = termeU1, relation = relation_recherchee, terme2 = termeU2).exists()) :
				if(Terme.objects.filter(id = termeU1).exists() and Terme.objects.filter(id = termeU2).exists()):
					RelationAVerifier.objects.create(terme1=Terme.objects.get(id=termeU1),relation=relation_recherchee,terme2=Terme.objects.get(id=termeU2),poids=0)
				
			return reponse
		else :
			reponse = random.choice(LIST_SAIS_PAS)
			if(relation_recherchee == "has_part"):
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.terme, relation = "has_part", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								reponse = "{} oui.".format(random.choice(LIST_OUI_FORT))
							elif(r.poids >= SAIS_PAS) :
								reponse = "{} oui.".format(random.choice(LIST_OUI_FAIBLE))
							else :
								reponse = random.choice(LIST_SAIS_PAS)
					else :
						reponse = "{}.".format(random.choice(LIST_SAIS_PAS))
			elif(relation_recherchee == "has_attribute") :
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "has_attribute", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								reponse = "{} oui.".format(random.choice(LIST_OUI_FORT))
							elif(r.poids >= SAIS_PAS) :
								reponse = "{} oui.".format(random.choice(LIST_OUI_FAIBLE))
							else :
								reponse = random.choice(LIST_SAIS_PAS)
					else :
						reponse = "{}.".format(random.choice(LIST_SAIS_PAS))
			else:	
				reponse = "{}.".format(random.choice(LIST_SAIS_PAS))
			listAverifier = RelationAVerifier.objects.filter(terme1 = termeU1, relation = relation_recherchee, terme2 = termeU2)
			if(len(listAverifier) == 0) :
				existeTermBool = Terme.objects.filter(id = termeU1).exists() and Terme.objects.filter(id = termeU2).exists()
				if(existeTermBool):
					RelationAVerifier.objects.create(terme1=Terme.objects.get(id=termeU1),relation=relation_recherchee,terme2=Terme.objects.get(id=termeU2),poids=0)
	return reponse



def searchRelationPourquoi(termeU1,relation_recherchee,termeU2) :
	#termeU1 = toSingular(termeU1)
	#termeU2 = toSingular(termeU2)
	find = False
	listRelations = Relation.objects.filter(terme1= termeU1, relation = relation_recherchee)
	for rel in listRelations :
		p1 = rel.poids
		listRelations2 = Relation.objects.filter(terme2= termeU2, relation = relation_recherchee, terme1 = rel.terme2.id)
		for rel2 in listRelations2 :
			p2 = rel2.poids
			if(p1 >= OUI_FAIBLE and p2 >= OUI_FAIBLE) :
				termeC1 = Terme.objects.get(id = termeU1).terme
				termeC2 = rel.terme2.terme
				termeC3 = Terme.objects.get(id = termeU2).terme
				if(relation_recherchee == "is_a") :
					reponse = "peut être parce que {} est sous-classe de {}, qui est sous-classe de {} ".format(termeC1,termeC2,termeC3)
				elif(relation_recherchee == "has_part") :
					reponse = "peut être parce que {} est composé de {}, qui est composé de {} ".format(termeC1,termeC2,termeC3)
				elif(relation_recherchee == "has_attribute") :
					reponse = "peut être parce que {} peut avoir comme propriété {}, qui peut avoir comme propriété {} ".format(termeC1,termeC2,termeC3)

				return reponse
				poids = OUI_FAIBLE
				find = False
			elif((p1 < OUI_FAIBLE and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < OUI_FAIBLE)) :
				if((p1 >= SAIS_PAS and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= SAIS_PAS)) :
					return "Je ne suis pas certain de cela"
					poids = SAIS_PAS
					find = False
				elif((p1 >= NON_FAIBLE and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FAIBLE)) :
					return "Aucune idée"
					poids = 0
					find = False
				elif((p1 >= NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FORT)) :
					return "j'en doute que cela soit le cas"
					poids = -3
					find = False
				elif((p1 < NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < NON_FORT)) :
					return "Impossible, a mon avis c'est tout le contraire"
					poids = -11
					find = False
	listRelations = Relation.objects.filter(terme1= termeU1, relation = relation_recherchee, terme2 = termeU2)
	for rel in listRelations :
		if (rel.poids < NON_FORT):
			find = True
			return random.choice(LIST_NON_FORT)
		elif(rel.poids < NON_FAIBLE):
			find = True
			return random.choice(LIST_NON_FAIBLE)
		elif(rel.poids < SAIS_PAS) :
			find = True
			return random.choice(LIST_SAIS_PAS)
		elif(rel.poids < OUI_FAIBLE) :
			find = True
		else :
			find = True
	if(find == False) :
		return random.choice(LIST_SAIS_PAS)
	else :
		if(relation_recherchee == "has_part"):
			list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
			for rel in list_relation_has_part :
				relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "has_part", terme2 = termeU2)
				if len(relation) > 0:
					for r in relation :
						if(r.poids >= OUI_FAIBLE) :
							termeC1 = Terme.objects.get(id = termeU1).termee
							termeC2 = rel.terme2.terme
							termeC3 = Terme.objects.get(id = termeU2).terme
							reponse = "peut être parce que {} est sous-classe de {}, qui est composé de {} ".format(termeC1,termeC2,termeC3)
							return reponse
						elif(r.poids >= SAIS_PAS) :
							return "{} oui.".format(random.choice(LIST_OUI_FAIBLE))
						else :
							return "{} ".format(random.choice(LIST_SAIS_PAS))
				else :
					return "{}.".format(random.choice(LIST_SAIS_PAS))
			return "has_part"
		elif(relation_recherchee == "has_attribute") :
			list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
			for rel in list_relation_has_part :
				relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "has_attribute", terme2 = termeU2)
				if len(relation) > 0:
					for r in relation :
						if(r.poids >= OUI_FAIBLE) :
							termeC1 = Terme.objects.get(id = termeU1).terme
							termeC2 = rel.terme2.terme
							termeC3 = Terme.objects.get(id = termeU2).terme
							reponse = "peut être parce que {} est sous-classe de {}, qui possède comme propriété {} ".format(termeC1,termeC2,termeC3)
							return reponse
						elif(r.poids >= SAIS_PAS) :
							return "{} oui.".format(random.choice(LIST_OUI_FAIBLE))
						else :
							return "{}.".format(random.choice(LIST_SAIS_PAS))
				else :
					return "{} ".format(random.choice(LIST_SAIS_PAS))
			return "has_attribute"

		else:	
			return "{} ".format(random.choice(LIST_EVIDENT))




def construireQuestion(rav) :
	if(rav[1] == "is_a") :
		corpMsg = random.choice(LIST_IS_A)
	elif(rav[1] == "has_part") :
		corpMsg = random.choice(LIST_HAS_PART)
	elif(rav[1] == "has_attribute") :
		corpMsg = random.choice(LIST_HAS_ATTRIBUTE)

	termeUn = Terme.objects.get(id = rav[0]).terme
	termeDeux = Terme.objects.get(id = rav[2]).terme
	return "est-ce que {} {} {} ?".format(termeUn, corpMsg, termeDeux)



def chercherQuestion() :
	rav = RelationAVerifier.objects.order_by('?').first()
	return [rav.terme1.id, rav.relation, rav.terme2.id]


def chercherRelationTermeUtilisateur(terme) :
	idTerme = Terme.objects.get(terme = terme, raffinement = RAFFINEMENT).id
	rav = RelationAVerifier.objects.filter(Q(terme1=idTerme) | Q(terme2=idTerme)).order_by('?').first()
	return [rav.terme1.id, rav.relation, rav.terme2.id]


def traitement_reponse(rav, reponse) :
	reponse = reponse.lower()
	if(reponse in LIST_REPONSE_OUI_FORT):
		poid = OUI_FAIBLE
		RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		rep = "T'as repondu oui"
	elif(reponse in LIST_REPONSE_OUI_FAIBLE) :
		poid = SAIS_PAS
		RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		rep = "Tu dis oui faible"
	elif(reponse in LIST_REPONSE_SAIS_PAS) :
		poid = NON_FAIBLE
		RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		rep = "Tu dis que tu ne sais pas"
	elif(reponse in LIST_REPONSE_NON_FORT) :
		poid = NON_FORT - 1
		RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		rep = "Tu dis que c'est non"
	elif(reponse in LIST_REPONSE_NON_FAIBLE) :
		poid = NON_FORT
		RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		rep = "Tu dis non faible"
	else :
		return traitement_phrase(reponse)

	listRelationAVerifier = RelationAVerifier.objects.filter(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
	if(len(listRelationAVerifier) >= NOMBRE_VALIDATION_RELATION):
		Relation.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		RelationAVerifier.objects.filter(terme1=rav[0],relation = rav[1],terme2=rav[2]).delete()

	return rep 




def traitement_phrase(message):
    message = message.lower()
    list = message.split()
    print(list)
    
    if(list[0] == "est-ce" and list[1][0] == "q" and list[1][1] == "u"):
        """ Question du style est-ce qu.......
                """
        
        if (isADeterminant(list[2])) :
            """ phrase du style est-ce que un/une .........
                """
            i = 3
        else :
            """ phrase du style est-ce que/qu'une/qu'un .....
                """
            i = 2    

        compris = True
        if((list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2]) and list[i+3] == "sous-classe") or \
            (list[i+1] in LIST_CONJ_APPARTENIR and list[i+2] == "à" and list[i+3] == "la" and list[i+4] == "classe")or \
            (list[i+1] in LIST_CONJ_ETRE and list[i+2] == "sous-classe") or (list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2]))) :
            """ Question du style K est {une/un} sous-classe/appartient à la classe
                Relation is_a
                """

            if(list[i+1] in LIST_CONJ_ETRE and (list[i+2] == "sous-classe" or list[i+3] == "sous-classe")) :
                """Question formulée de la premiére façon
                    """
                j = i+5
                if (isADeterminant(list[i+2]) == False):
                    """est sous-classe
                        """
                    j -= 1
            elif(list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2])):
            	j = i+3

            else :
                """Question formulée de la deuxiemme façon
                    """
                j = i+6
            if(isADeterminant(list[j])) :
                j += 1    

            relation_recherchee = "is_a"            



        elif((list[i+1] in LIST_CONJ_ETRE and list[i+2] == "composé") or \
            (list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2]) and list[i+3] == "partie")) :
            """Question du style K est composé/ est une partie ......
                Relation has_part
                """
            if(list[i+2] == "composé") :
                """Question du style K est composé de....
                    """
                j = i+4
                if (isADeterminant(list[j])):
                    j += 1
            else :
                """Question du style K' est une partie de .....
                    """        
                j = i+5
                if (isADeterminant(list[j])):
                    j += 1
                if(list[j][len(list[j])-1] == '?'):
                	list[j] = list[j][0:len(list[j])-1]
                (i,j) = (j,i)    
            relation_recherchee = "has_part"

        
        elif(list[i+1]=="peut" and (list[i+2] == "etre" or list[i+2] == "être") and not(re.search(list[i+3], r"qualifiée?") is None) or \
            (list[i+1]=="peut" and list[i+2]=="avoir" and list[i+3]=="comme" and list[i+4]=="propriété")):
            """Question du style K peut etre qualifié(e)/ peut avoir comme propriété .....
                Relation has-attribute
                """
            if(list[i+2] == "avoir") :
                """Question peut avoir comme propriété .....
                    """
                j = i+5
            else :
                """Question peut etre qualifié(e)
                    """
                j = i+5
            if(isADeterminant(list[j])) :
                j += 1
            relation_recherchee = "has_attribute"        


        else :
            """Question non comprise
                """
            return "Je ne comprends pas votre question"
            compris = False   
        
        if(compris) :
            print("Vous cherchez une relation {} {} {}".format(list[i],relation_recherchee,list[j]))
            #termeU1 = Terme(list[i])
            teU1 = separateurSymboleTerme(list[i])
            existeTerme1 = existTerme(teU1)
            if(existeTerme1 != -1) :
                #termeU2 = Terme(list[j])
                teU2 = separateurSymboleTerme(list[j])
                existeTerme2 = existTerme(teU2)
                if(existeTerme2 != -1) :
                    """On reconnait les deux termes que l'utilisateur à introduit
                    On cherche si la relation entre les deux existe """

                    print("Je connais les deux termes")
                    #print(searchRelation(teU1,relation_recherchee,teU2))
                    return searchRelation(existeTerme1,relation_recherchee,existeTerme2)
                else :
                    """Le deuxiemme Terme est inconnu
                        """
                    return "Je ne connais pas ce qu'est {}".format(teU2)       
            else :
                """Le Premier Terme est inconnu
                    """
                return "Je ne connais pas ce qu'est {}".format(list[i])







    elif(list[0] == "pourquoi") :
    	#Question du style Pourquoi ... ?



        if (list[1] == "est-ce" and list[2] == "que") :
            """ phrase du style est-ce que un/une .........
                """
            i = 3
        else :
            """ phrase du style est-ce que/qu'une/qu'un .....
                """
            i = 1 

        if(isADeterminant(list[i])) :
        	i += 1   

        compris = True
        if((list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2]) and list[i+3] == "sous-classe") or \
            (list[i+1] in LIST_CONJ_APPARTENIR and list[i+2] == "à" and list[i+3] == "la" and list[i+4] == "classe")or \
            (list[i+1] in LIST_CONJ_ETRE and list[i+2] == "sous-classe") or (list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2]))) :
            """ Question du style K est {une/un} sous-classe/appartient à la classe
                Relation is_a
                """

            if(list[i+1] in LIST_CONJ_ETRE and (list[i+2] == "sous-classe" or list[i+3] == "sous-classe")) :
                """Question formulée de la premiére façon
                    """
                j = i+5
                if (isADeterminant(list[i+2])):
                    """est sous-classe
                        """
                    j -= 1
            elif(list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2])):
            	j = i+3
            else :
                """Question formulée de la deuxiemme façon
                    """
                j = i+6
            if(isADeterminant(list[j])) :
                j += 1    

            relation_recherchee = "is_a"            



        elif((list[i+1] in LIST_CONJ_ETRE and list[i+2] == "composé") or \
            (list[i+1] in LIST_CONJ_ETRE and isADeterminant(list[i+2]) and list[i+3] == "partie")) :
            """Question du style K est composé/ est une partie ......
                Relation has_part
                """
            if(list[i+2] == "composé") :
                """Question du style K est composé de....
                    """
                j = i+4
                if (isADeterminant(list[j])):
                    j += 1
            else :
                """Question du style K' est une partie de .....
                    """        
                j = i+5
                if (isADeterminant(list[j])):
                    j += 1
                if(list[j][len(list[j])-1] == '?'):
                	list[j] = list[j][0:len(list[j])-1]
                (i,j) = (j,i)    
            relation_recherchee = "has_part"

        
        elif(list[i+1]=="peut" and (list[i+2] == "etre" or list[i+2] == "être") and not(re.search(list[i+3], r"qualifiée?") is None) or \
            (list[i+1]=="peut" and list[i+2]=="avoir" and list[i+3]=="comme" and list[i+4]=="propriété")):
            """Question du style K peut etre qualifié(e)/ peut avoir comme propriété .....
                Relation has-attribute
                """
            if(list[i+2] == "avoir") :
                """Question peut avoir comme propriété .....
                    """
                j = i+5
            else :
                """Question peut etre qualifié(e)
                    """
                j = i+5
                if(isADeterminant(list[j])) :
                    j += 1
            relation_recherchee = "has_attribute"        


        else :
            """Question non comprise
                """
            return "Je ne comprends pas votre question"
            compris = False   
        
        if(compris) :
            #termeU1 = Terme(list[i])
            teU1 = separateurSymboleTerme(list[i])
            teU2 = separateurSymboleTerme(list[j])
            print("Vous cherchez une relation {} {} {}".format(teU1,relation_recherchee,teU2))
            existeTerme1 = existTerme(teU1)
            if(existeTerme1 != -1) :
                #termeU2 = Terme(list[j])
                existeTerme2 = existTerme(teU2)
                if(existeTerme2 != -1) :
                    """On reconnait les deux termes que l'utilisateur à introduit
                    On cherche si la relation entre les deux existe """

                    print("Je connais les deux termes")
                    return searchRelationPourquoi(existeTerme1,relation_recherchee,existeTerme2)
                else :
                    """Le deuxiemme Terme est inconnu
                        """
                    return "Je ne connais pas ce qu'est {}".format(teU2)       
            else :
                """Le Premier Terme est inconnu
                    """
                return "Je ne connais pas ce qu'est {}".format(teU1)
    elif ((list[0] == "posez" or list[0] == "pose") and ("question" in list or "questions" in list)):
    	return chercherQuestion()
    elif((list[0] == "parle" and list[1] == "moi" and list[2] == "de") or (list[0] == "parlons" and list[1] == "de")) :
    	if(list[0] == "parle"):
    		i = 3
    	else:
    		i = 2
    	if(existTerme(list[i])):
    		return chercherRelationTermeUtilisateur(list[i])
    	else:
    		return "je ne sais pas ce qu'est {} ".format(list[i])

    else:
        """Ceci n'est peut etre pas une question
            """
        return "{} est une question ? ".format(message)

