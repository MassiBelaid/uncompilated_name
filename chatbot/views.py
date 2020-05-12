from django.shortcuts import render
from django.http import HttpResponse
from datetime import date
from chatbot.models import Terme,Relation,RelationAVerifier
import re
import random
from django.db.models import Q
from django.db import transaction
import urllib.request
from threading import Thread



NON_FORT = -10
NON_FAIBLE = -2
SAIS_PAS = 5
OUI_FAIBLE = 15
NOMBRE_VALIDATION_RELATION = 2

LIST_IS_A = ["est un", "est une sous-classe de", "est un sous-ensemble de", "appartient à la classe de"]
LIST_HAS_PART = ["est composé de", "a comme partie"]
LIST_HAS_ATTRIBUTE = ["peut être qualifié de", "peut avoir comme propriété","a comme propriété"]
LIST_OWN = ["possède"]

LIST_QUE_VEUX_TU_SAVOIR = ["Si tu veux savoir autre chose, je t'écoute.", "Si tu as besoin de savoir quelque chose, je t'en prie.", "Si tu as besoin de savoir quelque chose, je t'écoute."]
LIST_FAIRE_CONNAISSANCE = ["faisons connaissance","apprenons à nous connaitre","apprenons a nous connaitre","apprenons à nous connaître"]

LIST_OUI_FORT = ["certainement","sûrement","absolument","oui c'est certain","oui c'est sûr","assurément oui"]
LIST_OUI_FAIBLE = ["en majorité oui","globalement oui","probablement oui","oui dans beaucoup de cas","oui mais pas toujours"]
LIST_SAIS_PAS = ["peut-être","je ne sais pas", "je sais pas","aucune idée","je ne pense pas","je pense pas","je ne suis pas sûr","je ne crois pas","je crois pas"]
LIST_NON_FORT = ["absolument pas","impossible","pas du tout"]
LIST_NON_FAIBLE = ["plutôt pas","peut-être pas","j'en doute","je ne crois pas"]

LIST_REPONSE_OUI_FORT = ["oui certainement","oui sûrement","oui absolument","oui surement","oui","absolument","surement","sûrement","assurément","assurément oui","assurement","assurement oui","bah oui","ben oui"]
LIST_REPONSE_OUI_FAIBLE = ["oui en majorité","oui globalement","oui probablement","oui dans beaucoup de cas","oui en majorite","eventuellement","parfois","oui parfois","parfois oui"]
LIST_REPONSE_SAIS_PAS = ["peut-être","peut etre", "peut être","pas toujours","pas forcément","pas forcement","peut-etre","je ne suis pas sur","je ne suis pas sûr","je ne crois pas","je crois pas","je ne pense pas","je pense pas","je sais pas","je ne sais pas"]
LIST_REPONSE_NON_FAIBLE = ["plutôt pas","peut-être pas","j'en doute","je ne crois pas","plutot pas","peut-etre pas"]
LIST_REPONSE_NON_FORT = ["absolument pas","impossible","pas du tout","non","absolument non"]

LIST_EVIDENT = ["parce que c'est évident", "c'est factuel","parce ce que c'est un fait","c'est évident"]

LIST_DETERMINANT = ["un","une","des","la","le","les"]
LIST_ALORS = ["alors","du coup","de ce fait","par conséquent","donc"]
LIST_BONJOUR = ["salut","bonjour","coucou","hello","bonsoir","hey"]
LIST_CA_VA = ["ça va", "sa va", "ca va", "comment vas-tu", "comment allez-vous","comment vas tu", "comment allez vous", "comment ça va", "comment ca va"]
LIST_PARLE = ["parle","parlez","parlons","parles"]

LIST_CONJ_ETRE = ["est","sont"]
LIST_CONJ_APPARTENIR = ["appartient","appartiennent"]

STOP_WORDS = ["un","une","des","la","le","les","ton","ta","tes","sa","ses","son","de","des","le","les","la","à","a",",",";","!",":","?","un","une","qu'un","qu'une",
"que","appartient","appartiennent","est","sont","peut","avoir","comme","etre","être","moi"]

RAFFINEMENT = "nul0"

LIST_MOT_A_EVITER = ["ton","ta","tes","sa","ses","son","de","des","le","les","la","à","a",",",";","!",":","?"]


def home(request):
	today = date.today()
	phrase = request.GET.get('phrase') or ''
	rav = request.session.get('question')
	dialog = request.session.get('dialog')
	if(dialog is None) :
		dialog = []
	if (rav is not None) :
		if(phrase == '') :
			request.session['question'] = None
			return render(request,'chatbot/chatbot.html',{'date':today, 'reponse':"Bonjour, je suis Greg. Que veux-tu savoir ?",'dialog':dialog})
		else :
			dialog.insert(0,phrase)
			if(rav[0] == "4"):
				liste_retour_raffinement = reponse_dialog_raffinement(rav,phrase,request)
				if(type(liste_retour_raffinement) == str):
					dialog.insert(0,liste_retour_raffinement)
					request.session['dialog'] = dialog
					return render(request,'chatbot/chatbot.html',{'date':today,'reponse':liste_retour_raffinement,'dialog':dialog})
				elif(liste_retour_raffinement is not False) :
					if(len(liste_retour_raffinement[1]) == 0):
						request.session['question'] = None
						rep = liste_retour_raffinement[3]
					else :
						request.session['question'] = liste_retour_raffinement
						rep = liste_retour_raffinement[4]
					dialog.insert(0,rep)
					request.session['dialog'] = dialog
					return render(request,'chatbot/chatbot.html',{'date':today,'reponse':rep,'dialog':dialog})

			else :
				reponse = traitement_reponse(rav, phrase,request)
				request.session['question'] = None
				if(type(reponse) == str) :
					dialog.insert(0,reponse)
					request.session['dialog'] = dialog
					return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse,'dialog':dialog})
				else :
					if(reponse[0] == "4"):
						liste_retour_raffinement = dialog_raffinement(reponse)
						dialog.insert(0,liste_retour_raffinement[4])
						request.session['dialog'] = dialog
						print(liste_retour_raffinement[1])
						if(len(liste_retour_raffinement[1]) == 0):
							request.session['question'] = None
							rep = liste_retour_raffinement[3]
							dialog.insert(0,rep)
							request.session['dialog'] = dialog
							return render(request,'chatbot/chatbot.html',{'date':today,'reponse':rep,'dialog':dialog})
						else :
							request.session['question'] = liste_retour_raffinement
							rep = liste_retour_raffinement[4]
							dialog.insert(0,rep)
							request.session['dialog'] = dialog
						return render(request,'chatbot/chatbot.html',{'date':today,'reponse':rep,'dialog':dialog})
					else :
						request.session['question'] = reponse
						reponse = construireQuestion (reponse)
						dialog.insert(0,reponse)
						request.session['dialog'] = dialog
						return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse,'dialog':dialog})	

	if(phrase == '') :
		request.session['dialog'] = dialog
		return render(request,'chatbot/chatbot.html',{'date':today, 'reponse':"Bonjour, je suis Greg. Que veux-tu savoir ?",'dialog':dialog})
	else :
		dialog.insert(0,phrase)
		reponse = traitement_phrase(phrase,request)
		print("_______________reponse : {} ".format(reponse))
		if(type(reponse) == str) :
			dialog.insert(0,reponse)
			request.session['dialog'] = dialog
			return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse,'dialog':dialog})
		else :
			if(reponse[0] == "4"):
				liste_retour_raffinement = dialog_raffinement(reponse)
				request.session['question'] = reponse
				return render(request,'chatbot/chatbot.html',{'date':today,'reponse':liste_retour_raffinement[4],'dialog':dialog})
			else :
				request.session['question'] = reponse
				reponse = construireQuestion (reponse)
				dialog.insert(0,reponse)
				request.session['dialog'] = dialog
				return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse,'dialog':dialog})









def extraire(terme) :
	LIST_ALL = []
	
	LIST_ALL1 = extraireJDM(terme,"1")
	LIST_ALL6 = extraireJDM(terme,"6")
	LIST_ALL9 = extraireJDM(terme,"9")
	LIST_ALL17 = extraireJDM(terme,"17")
	LIST_ALL121 = extraireJDM(terme,"121")


	try :
		LIST_ALL_RELATIONS = LIST_ALL1[1] + LIST_ALL6[1] + LIST_ALL9[1] + LIST_ALL17[1] + LIST_ALL121[1]
		LIST_ALL_TERMES = LIST_ALL1[0] + LIST_ALL6[0] + LIST_ALL9[0] + LIST_ALL17[0] + LIST_ALL121[0]

		idT = LIST_ALL1[2][0]

		print("Sa taillleeeee oooooooooooooo {}".format(len(LIST_ALL_RELATIONS)))
		Relation.objects.bulk_create(LIST_ALL_RELATIONS, ignore_conflicts = True)


		return idT
	except Exception :
		return -1










def extraireJDM(terme, numRel) :
	LIST_ALL = [[],[],[]]
	idDuTerme = -1
	termeURL = terme.replace("é","%E9").replace("è","%E8").replace("ê","%EA").replace("à","%E0").replace("ç","%E7").replace("û","%FB").replace(" ","+")
	try :
		with urllib.request.urlopen("http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={}&rel={}".format(termeURL,numRel)) as url :
			s = url.read().decode('ISO-8859-1')
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
								if(len(caseDuTerme.split(">")[0]) < 100 and int(casesTermes[4]) > 50 ):
									try :
										Terme.objects.create(id = casesTermes[1], terme = caseDuTerme.split(">")[0], raffinement = caseDuTerme.split(">")[1], importe = "0")
										LIST_ALL[0].append(Terme(id = casesTermes[1], terme = caseDuTerme.split(">")[0], raffinement = caseDuTerme.split(">")[1], importe = "0"))
									except Exception:
										print("term ignored {} =======================================".format(caseDuTerme))
									
					elif(len(casesTermes) == 5 and not("=" in casesTermes[2])) :
						id = casesTermes[1]
						caseDuTerme = casesTermes[2]
						caseDuTerme = caseDuTerme[1: len(caseDuTerme)-1]
						if(caseDuTerme.lower() == terme and len(caseDuTerme) < 100) :
							idDuTerme = casesTermes[1]
							LIST_ALL[2].append(idDuTerme)
							Terme(id = idDuTerme, terme = caseDuTerme, raffinement = RAFFINEMENT).delete()
							try :
								Terme.objects.create(id = idDuTerme, terme = caseDuTerme, raffinement = RAFFINEMENT, importe = "1")
								LIST_ALL[0].append(Terme(id = idDuTerme, terme = caseDuTerme, raffinement = RAFFINEMENT, importe = "1"))
							except Exception:
								print("term ignored {} =======================================".format(caseDuTerme))
						else :
							if(not Terme.objects.filter(id = casesTermes[1]).exists() and len(caseDuTerme) < 100 and int(casesTermes[4]) > 50):
								try :				
									Terme.objects.create(id = casesTermes[1], terme = caseDuTerme, raffinement = RAFFINEMENT, importe = "0")
									LIST_ALL[0].append(Terme(id = casesTermes[1], terme = caseDuTerme, raffinement = RAFFINEMENT, importe = "0"))
								except Exception:
									print("term ignored {} =======================================".format(caseDuTerme))
								

				for ligne in listTouteRelation :
					casesRelation = ligne.split(";")
					if(len(casesRelation) == 6):
						if(numRel == "1") :
							r = "raff_sem"
						elif(numRel == "6") :
							r = "is_a"
						elif(numRel == "9") :
							r = "has_part"
						elif(numRel == "17") :
							r = "has_attribute"
						elif(numRel == "121") :
							r = "own"
						existeTermBool = Terme.objects.filter(id = casesRelation[3]).exists() and Terme.objects.filter(id = casesRelation[2]).exists() and not Relation.objects.filter(terme1 = Terme.objects.get(id = casesRelation[2]), terme2 = Terme.objects.get(id = casesRelation[3]), relation = r).exists()
						#print(" ============== ================== == = = = ={}       {}   le terme existe : {}".format(terme, r, existeTermBool))
						if(existeTermBool and (int(casesRelation[5]) < -4 or int(casesRelation[5]) > 4)):
							try :
								relationAjoutée = Relation(relation = r, source = "JDM", poids = casesRelation[5], terme1 = Terme.objects.get(id = casesRelation[2]), terme2 = Terme.objects.get(id = casesRelation[3]))
								if(relationAjoutée not in LIST_ALL[1]) :
									LIST_ALL[1].append(relationAjoutée)
									#print("JENTREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE    {}     {}    {}".format(r,casesRelation[3],casesRelation[2]))
									#Relation(relation = r, source = "JDM", poids = casesRelation[5], terme1 = Terme.objects.get(id = casesRelation[2]), terme2 = Terme.objects.get(id = casesRelation[3])).save()
								else :
									print("RELATION {} {} {} ========= IGNORED".format(casesRelation[2],r,casesRelation[3]))
							except Exception :
								print("relation ignored {} =======================================".format(r))
				return LIST_ALL
			else :
				return LIST_ALL
	except Exception :
		print("C CHAUD COMME DIS ALEXY")
		return LIST_ALL

		








def dialog_raffinement(tab_raffinement):
	nouvelle_liste_retour = []
	nouvelle_liste_retour.append("4")
	liste_des_raffinement = tab_raffinement[1]
	terme_raf_terme = liste_des_raffinement[0]
	#terme_raf_terme = liste_des_raffinement.pop(0)
	nouvelle_liste_retour.append(liste_des_raffinement)
	nouvelle_liste_retour.append(tab_raffinement[2])
	nouvelle_liste_retour.append(tab_raffinement[3])
	nouvelle_liste_retour.append("veux tu parler de {} ({})".format(tab_raffinement[2],terme_raf_terme))
	return nouvelle_liste_retour










def reponse_dialog_raffinement(tab_raffinement,reponse = "non",request = None) :
	nouvelle_liste_retour = []
	nouvelle_liste_retour.append("4")
	if(reponse in LIST_REPONSE_OUI_FORT):
		nouvelle_liste_retour.append([])
		nouvelle_liste_retour.append(tab_raffinement[2])
		nouvelle_liste_retour.append("alors {}".format(random.choice(LIST_OUI_FORT)))
		nouvelle_liste_retour.append("alors {}".format(random.choice(LIST_OUI_FORT)))
		return nouvelle_liste_retour
	elif(reponse in LIST_REPONSE_NON_FORT):
		liste_des_raffinement = tab_raffinement[1]
		#terme_raf_terme = liste_des_raffinement[0]
		terme_raf_terme = liste_des_raffinement.pop(0)
		if(len(liste_des_raffinement) > 0):
			nouvelle_liste_retour.append(liste_des_raffinement)
			nouvelle_liste_retour.append(tab_raffinement[2])
			nouvelle_liste_retour.append(tab_raffinement[3])
			nouvelle_liste_retour.append("veux tu parler de {} ({})".format(tab_raffinement[2],liste_des_raffinement[0]))
			return nouvelle_liste_retour
		else :
			nouvelle_liste_retour.append(liste_des_raffinement)
			nouvelle_liste_retour.append(tab_raffinement[2])
			nouvelle_liste_retour.append(tab_raffinement[3])
			nouvelle_liste_retour.append(tab_raffinement[3])
			return nouvelle_liste_retour
	else :
		request.session['question'] = None
		return False








def isADeterminant(det):
	if(det in LIST_DETERMINANT) :
		return True
	else :
		return False





def isAMotAEviter(mot):
	if(mot in LIST_MOT_A_EVITER) :
		return True
	else :
		return False







def separateurSymboleTerme(mot) :
	if(len(mot) > 1) :
		if(mot[len(mot)-1] == '?') :
			mot = mot[0:len(mot)-1]
		if(mot[0] == 'l' and mot[1] == "\'") :
			mot = mot[2:len(mot)]
		if(mot[len(mot)-1] == ',') :
			mot = mot[0:len(mot)-1]
		if(mot[0] == "d" and mot[1] == "\'") :
			mot = mot[2:len(mot)]
	return mot










def existTerme(ter) :
    idTerme = -1
    if(Terme.objects.filter(terme = ter, raffinement = RAFFINEMENT, importe = "1").exists()) :
    	termeBDDl = Terme.objects.filter(terme = ter, importe = "1", raffinement = RAFFINEMENT).first()
    	idTerme = termeBDDl.id
    	print("__________________________________" + str(idTerme))
    if(idTerme == -1) :
    	idTerme = extraire(ter)
    return int(idTerme) 










def searchRelation(termeU1,relation_recherchee,termeU2) :

	find = False
	listRelations = Relation.objects.filter(terme1 = termeU1, relation = relation_recherchee, terme2 = termeU2)
	for rel in listRelations :
		find = True
		if (rel.poids < NON_FORT):
			resultatRaffinement = verif_raffinement(termeU1,relation_recherchee,termeU2)
			if(len(resultatRaffinement) == 0):
				return "{}. {}".format(random.choice(LIST_NON_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
			else:
				liste_des_raf_a_r = []
				liste_des_raf_a_r.append("4")
				liste_des_raf_a_r.append(resultatRaffinement)
				liste_des_raf_a_r.append(Terme.objects.get(id = termeU1).terme)
				liste_des_raf_a_r.append("{}, {}. {}".format(random.choice(LIST_ALORS).capitalize(),random.choice(LIST_NON_FORT),random.choice(LIST_QUE_VEUX_TU_SAVOIR)))
				return liste_des_raf_a_r
		elif(rel.poids < NON_FAIBLE):
			resultatRaffinement = verif_raffinement(termeU1,relation_recherchee,termeU2)
			if(len(resultatRaffinement) == 0):
				return "{}. {}".format(random.choice(LIST_NON_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
			else:
				liste_des_raf_a_r = []
				liste_des_raf_a_r.append("4")
				liste_des_raf_a_r.append(resultatRaffinement)
				liste_des_raf_a_r.append(Terme.objects.get(id = termeU1).terme)
				liste_des_raf_a_r.append("{}, {}. {}".format(random.choice(LIST_ALORS).capitalize(),random.choice(LIST_NON_FAIBLE),random.choice(LIST_QUE_VEUX_TU_SAVOIR)))
				return liste_des_raf_a_r
		elif(rel.poids < SAIS_PAS) :
			resultatRaffinement = verif_raffinement(termeU1,relation_recherchee,termeU2)
			if(len(resultatRaffinement) == 0):
				return "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
			else:
				liste_des_raf_a_r = []
				liste_des_raf_a_r.append("4")
				liste_des_raf_a_r.append(resultatRaffinement)
				liste_des_raf_a_r.append(Terme.objects.get(id = termeU1).terme)
				liste_des_raf_a_r.append("{}, {}. {}".format(random.choice(LIST_ALORS).capitalize(),random.choice(LIST_SAIS_PAS),random.choice(LIST_QUE_VEUX_TU_SAVOIR)))
				return liste_des_raf_a_r
		elif(rel.poids < OUI_FAIBLE) :
			return "{}. {}".format(random.choice(LIST_OUI_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		else :
			return "{}. {}".format(random.choice(LIST_OUI_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
	if(find == False) :
		listRelations = Relation.objects.filter(terme1= termeU1, relation = relation_recherchee)
		for rel in listRelations :
			p1 = rel.poids
			listRelations2 = Relation.objects.filter(terme2= termeU2, relation = relation_recherchee, terme1 = rel.terme2.id)
			for rel2 in listRelations2 :
				p2 = rel2.poids
				if(p1 >= OUI_FAIBLE and p2 >= OUI_FAIBLE) :
					reponse = "{}. {}".format(random.choice(LIST_OUI_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
					find = True
				elif((p1 < OUI_FAIBLE and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < OUI_FAIBLE)) :
					if((p1 >= SAIS_PAS and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= SAIS_PAS)) :
						reponse = "{}. {}".format(random.choice(LIST_OUI_FAIBLE),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
						find = True
					elif((p1 >= NON_FAIBLE and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FAIBLE)) :
						resultatRaffinement = verif_raffinement(termeU1,relation_recherchee,termeU2)
						if(len(resultatRaffinement) == 0):
							reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							poids = 0
							find = True
						else :
							liste_des_raf_a_r = []
							liste_des_raf_a_r.append("4")
							liste_des_raf_a_r.append(resultatRaffinement)
							liste_des_raf_a_r.append(Terme.objects.get(id = termeU1).terme)
							liste_des_raf_a_r.append("{}, {}. {}".format(random.choice(LIST_ALORS).capitalize(),random.choice(LIST_SAIS_PAS),random.choice(LIST_QUE_VEUX_TU_SAVOIR)))
							return liste_des_raf_a_r
					elif((p1 >= NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FORT)) :
						resultatRaffinement = verif_raffinement(termeU1,relation_recherchee,termeU2)
						if(len(resultatRaffinement) == 0):
							reponse = "{}. {}".format(random.choice(LIST_NON_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							poids = 0
							find = True
						else :
							liste_des_raf_a_r = []
							liste_des_raf_a_r.append("4")
							liste_des_raf_a_r.append(resultatRaffinement)
							liste_des_raf_a_r.append(Terme.objects.get(id = termeU1).terme)
							liste_des_raf_a_r.append("{}, {}. {}".format(random.choice(LIST_ALORS).capitalize(),random.choice(LIST_NON_FAIBLE),random.choice(LIST_QUE_VEUX_TU_SAVOIR)))
							return liste_des_raf_a_r
					elif((p1 < NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < NON_FORT)) :
							reponse = "{}. {}".format(random.choice(LIST_OUI_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							poids = 0
							find = True
					

		if(find) :
			if(RelationAVerifier.objects.filter(terme1 = termeU1, relation = relation_recherchee, terme2 = termeU2).exists()) :
				if(Terme.objects.filter(id = termeU1).exists() and Terme.objects.filter(id = termeU2).exists()):
					RelationAVerifier.objects.create(terme1=Terme.objects.get(id=termeU1),relation=relation_recherchee,terme2=Terme.objects.get(id=termeU2),poids=0)
				
			return reponse
		else :
			reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))


			if(relation_recherchee == "has_part"):
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "has_part", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								reponse = "{}. {}".format(random.choice(LIST_OUI_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							elif(r.poids >= SAIS_PAS) :
								reponse = "{}. {}".format(random.choice(LIST_OUI_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							else :
								reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
					else :
						reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))


			elif(relation_recherchee == "has_attribute") :
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "has_attribute", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								reponse = "{}. {}".format(random.choice(LIST_OUI_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							elif(r.poids >= SAIS_PAS) :
								reponse = "{}. {}".format(random.choice(LIST_OUI_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							else :
								reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
					else :
						reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))


			elif(relation_recherchee == "own") :
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "own", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								reponse = "{}. {}".format(random.choice(LIST_OUI_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							elif(r.poids >= SAIS_PAS) :
								reponse = "{}. {}".format(random.choice(LIST_OUI_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							else :
								reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
					else :
						reponse = "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
			else:
				resultatRaffinement = verif_raffinement(termeU1,relation_recherchee,termeU2)
				if(len(resultatRaffinement) == 0 ) :
					return "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
				else :
					liste_des_raf_a_r = []
					liste_des_raf_a_r.append("4")
					liste_des_raf_a_r.append(resultatRaffinement)
					liste_des_raf_a_r.append(Terme.objects.get(id = termeU1).terme)
					liste_des_raf_a_r.append("{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR)))
					return liste_des_raf_a_r
			listAverifier = RelationAVerifier.objects.filter(terme1 = termeU1, relation = relation_recherchee, terme2 = termeU2)
			if(len(listAverifier) == 0) :
				existeTermBool = Terme.objects.filter(id = termeU1).exists() and Terme.objects.filter(id = termeU2).exists()
				if(existeTermBool):
					RelationAVerifier.objects.create(terme1=Terme.objects.get(id=termeU1),relation=relation_recherchee,terme2=Terme.objects.get(id=termeU2),poids=0)
	return reponse














def searchRelationPourquoi(termeU1,relation_recherchee,termeU2) :
	find = False
	listRelations = Relation.objects.filter(terme1= termeU1, relation = relation_recherchee)
	for rel in listRelations :
		p1 = rel.poids
		listRelations2 = Relation.objects.filter(terme2= termeU2, relation = relation_recherchee, terme1 = rel.terme2.id)
		for rel2 in listRelations2 :
			p2 = rel2.poids
			print("...................................... P1 = {} .............. P2 = {}".format(p1,p2))
			if(p1 >= SAIS_PAS and p2 >= SAIS_PAS) :
				termeC1 = Terme.objects.get(id = termeU1).terme
				termeC2 = rel.terme2.terme
				termeC3 = Terme.objects.get(id = termeU2).terme
				if(relation_recherchee == "is_a") :
					reponse = "Je pense que c'est parce que {} est sous-classe de {}, qui est sous-classe de {}. {}".format(termeC1,termeC2,termeC3, random.choice(LIST_QUE_VEUX_TU_SAVOIR))
				elif(relation_recherchee == "has_part") :
					reponse = "Je pense que c'est parce que {} fait partie de {}, qui est composé de {}. {}".format(termeC1,termeC2,termeC3, random.choice(LIST_QUE_VEUX_TU_SAVOIR))
				elif(relation_recherchee == "has_attribute") :
					reponse = "Je pense que c'est parce que {} peut avoir comme propriété {}, qui peut avoir comme propriété {}. {}".format(termeC1,termeC2,termeC3, random.choice(LIST_QUE_VEUX_TU_SAVOIR))
				elif(relation_recherchee == "own") :
					reponse = "Je pense que c'est parce que {} peut possèder {}, qui peut possèder {}. {}".format(termeC1,termeC2,termeC3, random.choice(LIST_QUE_VEUX_TU_SAVOIR))

				return reponse


				poids = OUI_FAIBLE
				find = False
			elif((p1 < OUI_FAIBLE and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < OUI_FAIBLE)) :
				if((p1 >= SAIS_PAS and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= SAIS_PAS)) :
					return "Je ne suis pas certain de cela. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))

				elif((p1 >= NON_FAIBLE and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FAIBLE)) :
					return "Aucune idée. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))

				elif((p1 >= NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FORT)) :
					return "Je doute que cela soit le cas. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))

				elif((p1 < NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < NON_FORT)) :
					return "Impossible, à mon avis c'est tout le contraire. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))



	listRelations = Relation.objects.filter(terme1= termeU1, relation = relation_recherchee, terme2 = termeU2)
	for rel in listRelations :
		if (rel.poids < NON_FORT):
			find = True
			return "{}. {}".format(random.choice(LIST_NON_FORT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(rel.poids < NON_FAIBLE):
			find = True
			return "{}. {}".format(random.choice(LIST_NON_FAIBLE).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(rel.poids < SAIS_PAS) :
			find = True
			return "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(rel.poids < OUI_FAIBLE) :
			find = True
		else :
			find = True



	if(find == False) :
		return "{}. {}".format(random.choice(LIST_SAIS_PAS).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))

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
							reponse = "Peut être parce que {} est une sous-classe de {}, qui est composé de {}. {}".format(termeC1,termeC2,termeC3,random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							return reponse
						elif(r.poids >= SAIS_PAS) :
							termeC1 = Terme.objects.get(id = termeU1).termee
							termeC2 = rel.terme2.terme
							termeC3 = Terme.objects.get(id = termeU2).terme
							reponse = "Peut être parce que {} est une sous-classe de {}, qui est composé de {}. {}".format(termeC1,termeC2,termeC3,random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							return reponse



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
							reponse = "Peut être parce que {} est une sous-classe de {}, qui possède comme propriété {}. {}".format(termeC1,termeC2,termeC3,random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							return reponse
						elif(r.poids >= SAIS_PAS) :
							termeC1 = Terme.objects.get(id = termeU1).terme
							termeC2 = rel.terme2.terme
							termeC3 = Terme.objects.get(id = termeU2).terme
							reponse = "Peut être parce que {} est une sous-classe de {}, qui possède comme propriété {}. {}".format(termeC1,termeC2,termeC3,random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							return reponse
						

		elif(relation_recherchee == "own") :
			list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
			for rel in list_relation_has_part :
				relation = Relation.objects.filter(terme1 = rel.terme2.id, relation = "own", terme2 = termeU2)
				if len(relation) > 0:
					for r in relation :
						if(r.poids >= OUI_FAIBLE) :
							termeC1 = Terme.objects.get(id = termeU1).terme
							termeC2 = rel.terme2.terme
							termeC3 = Terme.objects.get(id = termeU2).terme
							reponse = "Peut être parce que {} est une sous-classe de {}, qui possède {}. {}".format(termeC1,termeC2,termeC3,random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							return reponse
						elif(r.poids >= SAIS_PAS) :
							termeC1 = Terme.objects.get(id = termeU1).terme
							termeC2 = rel.terme2.terme
							termeC3 = Terme.objects.get(id = termeU2).terme
							reponse = "Peut être parce que {} est une sous-classe de {}, qui possède {}. {}".format(termeC1,termeC2,termeC3,random.choice(LIST_QUE_VEUX_TU_SAVOIR))
							return reponse	


		return "{}. {}".format(random.choice(LIST_EVIDENT).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))















def verif_raffinement(terme1, r, terme2):
	print("========================================= JENTREEEEEEEEEEEEEEEEEEEEEEEEEEEEEE dans verif raffinement")
	result = []
	terme = Terme.objects.get(id = terme1)
	listTermesRaffinement = Terme.objects.filter(terme = terme.terme).exclude(raffinement = RAFFINEMENT)
	for tm in listTermesRaffinement :
		listRels = Relation.objects.filter(terme1 = tm.id, relation = r, terme2 = terme2)
		for relat in listRels :
			if(relat.poids > OUI_FAIBLE):
				result.append(tm.raffinement)
	return result











def construireQuestion(rav) :
	if(rav[1] == "is_a") :
		corpMsg = random.choice(LIST_IS_A)
	elif(rav[1] == "has_part") :
		corpMsg = random.choice(LIST_HAS_PART)
	elif(rav[1] == "has_attribute") :
		corpMsg = random.choice(LIST_HAS_ATTRIBUTE)
	elif(rav[1] == "own") :
		corpMsg = random.choice(LIST_OWN)

	termeUn = Terme.objects.get(id = rav[0]).terme
	termeDeux = Terme.objects.get(id = rav[2]).terme
	return "est-ce que {} {} {} ?".format(termeUn, corpMsg, termeDeux).capitalize()









def chercherQuestion() :
	if(RelationAVerifier.objects.filter().exists()) :
		rav = RelationAVerifier.objects.order_by('?').first()
		return [rav.terme1.id, rav.relation, rav.terme2.id, "1"]
	else :
		rav = Relation.objects.order_by('?').first()
		return [rav.terme1.id, rav.relation, rav.terme2.id, "2"]
	








def chercherRelationTermeUtilisateur(terme) :
	idTerme = Terme.objects.filter(terme = terme, raffinement = RAFFINEMENT).first().id
	if(RelationAVerifier.objects.filter(Q(terme1=idTerme) | Q(terme2=idTerme)).exists()) :
		rav = RelationAVerifier.objects.filter(Q(terme1=idTerme) | Q(terme2=idTerme)).order_by('?').first()
		return [rav.terme1.id, rav.relation, rav.terme2.id,"1"]
	else :
		rav = Relation.objects.filter(Q(terme1=idTerme) | Q(terme2=idTerme)).order_by('?').first()
		return [rav.terme1.id, rav.relation, rav.terme2.id,"2"]
	









def faireConnaissance(request) :
	infoUser = request.session.get("user")
	if(infoUser is None) :
		return "poser des questions"
	else :
		return "poser d'autres questions"











def traitement_reponse(rav, reponse,request = None) :
	reponseList = pre_traitement_phrase(reponse)
	reponse = " ".join(str(elm) for elm in reponseList)
	if(rav[3] == "1") :
		if(reponse in LIST_REPONSE_OUI_FORT):
			poid = OUI_FAIBLE
			RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
			rep = "D'accord, alors je note que c'est correct. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_OUI_FAIBLE) :
			poid = SAIS_PAS
			RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
			rep = "D'accord, je note ça comme parfois vrai. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_SAIS_PAS) :
			poid = NON_FAIBLE
			RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
			rep = "D'accord, nous sommes donc deux à ne pas savoir. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_NON_FORT) :
			poid = NON_FORT - 1
			RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
			rep = "D'accord, je note que ce n'est absolument pas le cas. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_NON_FAIBLE) :
			poid = NON_FORT
			RelationAVerifier.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
			rep = "D'accord, je note que ça peut ne pas être le cas. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		else :
			return traitement_phrase(reponse,request)

		listRelationAVerifier = RelationAVerifier.objects.filter(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid)
		if(len(listRelationAVerifier) >= NOMBRE_VALIDATION_RELATION):
			Relation.objects.create(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2]),poids=poid,source = "UN")
			RelationAVerifier.objects.filter(terme1=rav[0],relation = rav[1],terme2=rav[2]).delete()

		return rep



	elif(rav[3] == "2") :
		relationPosee = Relation.objects.filter(terme1=Terme.objects.get(id=rav[0]),relation = rav[1],terme2=Terme.objects.get(id=rav[2])).first()
		if(reponse in LIST_REPONSE_OUI_FORT):
			if(relationPosee.poids <= OUI_FAIBLE) :
				relationPosee.poids += 15
			rep = "D'accord, alors je note que c'est correct. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_OUI_FAIBLE) :
			if(relationPosee.poids >= OUI_FAIBLE) :
				relationPosee.poids -= 15
			elif(relationPosee.poids <= SAIS_PAS) :
				relationPosee.poids += 15
			rep = "D'accord, je note ça comme parfois vrai. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_SAIS_PAS) :
			rep = "D'accord, nous sommes donc deux à ne pas savoir. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_NON_FORT) :
			if(relationPosee.poids >= NON_FORT) :
				relationPosee.poids -= 15
			rep = "D'accord, je note que ce n'est absolument pas le cas. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		elif(reponse in LIST_REPONSE_NON_FAIBLE) :
			if(relationPosee.poids >= SAIS_PAS) :
				relationPosee.poids -= 15
			elif(relationPosee.poids <= NON_FORT) :
				relationPosee.poids += 15
			rep = "D'accord, je note que ça peut ne pas être le cas. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))
		else :
			return traitement_phrase(reponse,request)

		relationPosee.save()

		return rep











def pre_traitement_phrase(message):
	message = message.lower()
	listAvant = message.split()
	listApres = []
	for mot in listAvant :
		mot = separateurSymboleTerme(mot)
		if(mot not in STOP_WORDS) :
			listApres.append(mot)
	return listApres












def traitement_phrase(message,request = None):
    list = pre_traitement_phrase(message)
    print(list)

    try :


	    if(list[0] == "est-ce"):
	        """ Question du style est-ce qu.......
	                """
	        
	        i = 2
	        termeUI1 = list[1]
	        termeUI2 = ""    

	        compris = True
	        if(("classe" in list) or ("sous-classe" in list)) :
	            """ Question du style K est {une/un} sous-classe/appartient à la classe
	                Relation is_a
	                """

	            if("classe" in list):
	            	indexDetemRel = list.index("classe")
	            else :
	            	indexDetemRel = list.index("sous-classe")

	            while(i < indexDetemRel):
	            	termeUI1 = "{} {}".format(termeUI1,list[i])
	            	i += 1

	            j = indexDetemRel + 2
	            termeUI2 = list[indexDetemRel + 1]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1


	            relation_recherchee = "is_a"






	        elif(("composé" in list) or ("partie" in list) or ("composée" in list)) :
	            """Question du style K est composé/ est une partie ......
	                Relation has_part
	                """
	            if("composé" in list):
	            	indexDetemRel = list.index("composé")
	            elif("partie" in list):
	            	indexDetemRel = list.index("partie")
	            else :
	            	indexDetemRel = list.index("composée")

	            while(i < indexDetemRel):
	            	termeUI1 = "{} {}".format(termeUI1,list[i])
	            	i += 1

	            j = indexDetemRel + 2
	            termeUI2 = list[indexDetemRel + 1]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1


	            if("partie" in list):
	            	(termeUI1,termeUI2) = (termeUI2,termeUI1)

	            relation_recherchee = "has_part"




	        
	        elif(("propriété" in list) or ("qualifié" in list) or ("qualifiée" in list)):
	            """Question du style K peut etre qualifié(e)/ peut avoir comme propriété .....
	                Relation has-attribute
	                """
	            if("propriété" in list):
	            	indexDetemRel = list.index("propriété")
	            elif("qualifié" in list):
	            	indexDetemRel = list.index("qualifié")
	            else :
	            	indexDetemRel = list.index("qualifiée")

	            while(i < indexDetemRel):
	            	termeUI1 = "{} {}".format(termeUI1,list[i])
	            	i += 1

	            j = indexDetemRel + 2
	            termeUI2 = list[indexDetemRel + 1]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1

	            relation_recherchee = "has_attribute"


	        elif(("possède" in list) or ("possede" in list) or ("possèdent" in list) or ("posseder" in list) or ("possedent" in list)) :

	        	if("possède" in list):
	        		indexDetemRel = list.index("possède")
	        	elif("possede" in list):
	        		indexDetemRel = list.index("possede")
	        	elif("possede" in list):
	        		indexDetemRel = list.index("possèdent")
	        	elif("possedent" in list):
	        		indexDetemRel = list.index("possedent")
	        	else:
	        		indexDetemRel = list.index("posseder")  

	        	while(i < indexDetemRel):
	        		termeUI1 = "{} {}".format(termeUI1,list[i])
	        		i += 1

	        	j = indexDetemRel + 2
	        	termeUI2 = list[indexDetemRel + 1]
	        	while(j < len(list)):
	        		termeUI2 = "{} {}".format(termeUI2,list[j])
	        		j += 1

	        	relation_recherchee = "r_own"
	        else :
	        	termeUI1 = list[1]
	        	j = 3 
	        	termeUI2 = list[2]
	        	while(j < len(list)):
	        		termeUI2 = "{} {}".format(termeUI2,list[j])
	        		j += 1
	        	relation_recherchee = "is_a"
	        


	        print("Vous cherchez une relation {} {} {}".format(termeUI1,relation_recherchee,termeUI2))

	        existeTerme1 = existTerme(termeUI1)
	        if(existeTerme1 != -1) :

	            existeTerme2 = existTerme(termeUI2)
	            if(existeTerme2 != -1) :
	                """On reconnait les deux termes que l'utilisateur à introduit
	                On cherche si la relation entre les deux existe """

	                print("Je connais les deux termes")
	                #print(searchRelation(teU1,relation_recherchee,teU2))
	                return searchRelation(existeTerme1,relation_recherchee,existeTerme2)
	            else :
	                """Le deuxiemme Terme est inconnu
	                    """
	                return "Je ne connais pas ce qu'est {}".format(termeUI2)       
	        else :
	            """Le Premier Terme est inconnu
	                """
	            return "Je ne connais pas ce qu'est {}".format(termeUI1)








	    elif(list[0] == "pourquoi") :
	    	#Question du style Pourquoi ... ?



	        if (list[1] == "est-ce" ) :
	            """ phrase du style est-ce que un/une .........
	                """
	            i = 3
	            termeUI1 = list[2]
	            termeUI2 = ""
	        else :
	            """ phrase du style est-ce que/qu'une/qu'un .....
	                """
	            i = 2
	            termeUI1 = list[1]
	            termeUI2 = ""
	  

	        compris = True
	        if(("classe" in list) or ("sous-classe" in list)) :
	            """ Question du style K est {une/un} sous-classe/appartient à la classe
	                Relation is_a
	                """

	            if("classe" in list):
	            	indexDetemRel = list.index("classe")
	            else :
	            	indexDetemRel = list.index("sous-classe")

	            while(i < indexDetemRel):
	            	termeUI1 = "{} {}".format(termeUI1,list[i])
	            	i += 1

	            j = indexDetemRel + 2
	            termeUI2 = list[indexDetemRel + 1]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1
	            print(termeUI1)
	            print(termeUI2)

	            relation_recherchee = "is_a"           





	        elif(("composé" in list) or ("partie" in list) or ("composée" in list)) :
	            """Question du style K est composé/ est une partie ......
	                Relation has_part
	                """
	            if("composé" in list):
	            	indexDetemRel = list.index("composé")
	            elif("partie" in list):
	            	indexDetemRel = list.index("partie")
	            else :
	            	indexDetemRel = list.index("composée")

	            while(i < indexDetemRel):
	            	termeUI1 = "{} {}".format(termeUI1,list[i])
	            	i += 1

	            j = indexDetemRel + 2
	            termeUI2 = list[indexDetemRel + 1]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1
	            print(termeUI1)
	            print(termeUI2)


	            if("partie" in list):
	            	(termeUI1,termeUI2) = (termeUI2,termeUI1)
	            	
	            relation_recherchee = "has_part"




	        
	        elif(("propriété" in list) or ("qualifié" in list) or ("qualifiée" in list)):
	            """Question du style K peut etre qualifié(e) / peut avoir comme propriété / a comme propritété .....
	                Relation has-attribute
	                """
	            if("propriété" in list):
	            	indexDetemRel = list.index("propriété")
	            elif("qualifié" in list):
	            	indexDetemRel = list.index("qualifié")
	            else :
	            	indexDetemRel = list.index("qualifiée")

	            while(i < indexDetemRel):
	            	termeUI1 = "{} {}".format(termeUI1,list[i])
	            	i += 1

	            j = indexDetemRel + 2
	            termeUI2 = list[indexDetemRel + 1]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1
	            print(termeUI1)
	            print(termeUI2)
	            relation_recherchee = "has_attribute"






	        elif(("possède" in list) or ("possede" in list) or ("possèdent" in list) or ("posseder" in list) or ("possedent" in list)) :
	        	if("possède" in list):
	        		indexDetemRel = list.index("possède")
	        	elif("possede" in list):
	        		indexDetemRel = list.index("possede")
	        	elif("possede" in list):
	        		indexDetemRel = list.index("possèdent")
	        	elif("possedent" in list):
	        		indexDetemRel = list.index("possedent")
	        	else:
	        		indexDetemRel = list.index("posseder")  

	        	while(i < indexDetemRel):
	        		termeUI1 = "{} {}".format(termeUI1,list[i])
	        		i += 1

	        	j = indexDetemRel + 2
	        	termeUI2 = list[indexDetemRel + 1]
	        	while(j < len(list)):
	        		termeUI2 = "{} {}".format(termeUI2,list[j])
	        		j += 1

	        	print(termeUI1)
	        	print(termeUI2)
	        	relation_recherchee = "r_own"      




	        else :
	            """Question non comprise
	                """

	            termeUI1 = list[i-1]
	            j = i+1
	            termeUI2 = list[i]
	            while(j < len(list)):
	            	termeUI2 = "{} {}".format(termeUI2,list[j])
	            	j += 1
	            relation_recherchee = "is_a" 
	        



	        print("Vous cherchez une relation {} {} {}".format(termeUI1,relation_recherchee,termeUI2))
	        existeTerme1 = existTerme(termeUI1)
	        if(existeTerme1 != -1) :
	            #termeU2 = Terme(list[j])
	            existeTerme2 = existTerme(termeUI2)
	            if(existeTerme2 != -1) :
	                """On reconnait les deux termes que l'utilisateur à introduit
	                On cherche si la relation entre les deux existe """

	                print("Je connais les deux termes")
	                return searchRelationPourquoi(existeTerme1,relation_recherchee,existeTerme2)
	            else :
	                """Le deuxiemme Terme est inconnu
	                    """
	                return "Je ne connais pas ce qu'est {}".format(termeUI2)       
	        else :
	            """Le Premier Terme est inconnu
	                """
	            return "Je ne connais pas ce qu'est {}".format(termeUI1)








	    elif (("question" in list) or ("questions" in list) or ("questionne" in list) or ("questionnez" in list)):
	    	return chercherQuestion()


	    elif(("parle" in list) or ("parlons" in list) or ("parler" in list) or ("parles" in list)) :


	    	if("parle" in list) :
	    		indexDetemRel = list.index("parle") + 1
	    	elif("parlons" in list) :
	    		indexDetemRel = list.index("parlons") + 1
	    	elif("parler" in list) :
	    		indexDetemRel = list.index("parler") + 1
	    	elif("parles" in list) :
	    		indexDetemRel = list.index("parles") + 1


	    	if(len(list) == 1) :
	    		return faireConnaissance(request)
	    		
	    	elif(list[indexDetemRel] == "toi") :
	    		return "Eh bien, je m'appelle Greg, et puis... euh... Je suis timide. C'est tout. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))

	    	else :
	    		termeUI = list[indexDetemRel]
	    		indexDetemRel += 1

	    		while(indexDetemRel < len(list)):
	    			termeUI = "{} {}".format(termeUI, list[indexDetemRel])
	    			indexDetemRel += 1


	    		if(existTerme(termeUI)) :
	    			return chercherRelationTermeUtilisateur(termeUI)
	    		else:
	    			return "Je ne sais pas ce qu'est {}. {}".format(termeUI,random.choice(LIST_QUE_VEUX_TU_SAVOIR))





	    elif(list[0] in LIST_BONJOUR) :
	    	if(len(list)>3) :
	    		mess = "{} {} {}".format(list[1],list[2],list[3])
	    		if(mess in LIST_CA_VA) :
	    			return "{}, je vais bien merci. {}".format(random.choice(LIST_BONJOUR).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
	    		else :
	    			return "{}. {}".format(random.choice(LIST_BONJOUR).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
	    	elif(len(list)>2) :
	    		mess = "{} {}".format(list[1],list[2])
	    		if(mess in LIST_CA_VA) :
	    			return "{}, je vais bien merci. {}".format(random.choice(LIST_BONJOUR).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
	    		else :
	    			"{}. {}".format(random.choice(LIST_BONJOUR).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))
	    	else :
	    		return "{}. {}".format(random.choice(LIST_BONJOUR).capitalize(),random.choice(LIST_QUE_VEUX_TU_SAVOIR))


	    elif(message in LIST_FAIRE_CONNAISSANCE) :
	    	return faireConnaissance(request)


	    else:
	        """Ceci n'est peut etre pas une question
	            """
	        return "Je ne comprends pas encore ce que vous essayez de me dire. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))

    except Exception:
    	print("TU FAIS NIMPORTE QUOI YA ZEBI")
    	return "Je ne comprends pas encore ce que vous essayez de me dire. {}".format(random.choice(LIST_QUE_VEUX_TU_SAVOIR))























LIST_TERMES_A_EXTRAIRE = ["angle","armoire","banc","bureau","cabinet","carreau","chaise","classe","clé","coin","couloir","dossier","eau","école","écriture","entrée","escalier","étagère","étude",
"extérieur","fenêtre","intérieur","lavabo","lecture","lit","marche","matelas","maternelle","meuble","mousse","mur","peluche","placard","plafond","porte","portemanteau","poubelle","radiateur",
"rampe","récréation","rentrée","rideau","robinet","salle","savon","serrure","serviette","siège","sieste","silence","sol","sommeil","sonnette","sortie","table","tableau","tabouret","tapis",
"tiroir","toilette","vitre","absent","assis","bas","couché","haut","présent","crayon","stylo","feutre","taille-crayon","pointe","mine","gomme","dessin","coloriage","rayure","peinture","pinceau",
"couleur","craie","papier","feuille","cahier","carnet","carton","ciseaux","découpage","pliage","pli","colle","affaire","boîte","casier","caisse","trousse","cartable","jouet","jeu","pion","dé",
"domino","puzzle","cube","perle","chose","forme : carré","rond","pâte à modeler","tampon","livre","histoire","bibliothèque","image","album","titre","bande dessinée","conte","dictionnaire",
"magazine","catalogue","page","ligne","mot","enveloppe","étiquette","étiquette","alphabet","appareil","caméscope","cassette","cédé","cédérom","chaîne","chanson","chiffre","contraire","différence",
"doigt","écran","écriture","film","fois","idée","instrument","intrus","lettre","liste","magnétoscope","main","micro","modèle","musique","nom","nombre","orchestre","ordinateur","photo","point",
"poster","pouce","prénom","question","radio","sens","tambour","télécommande","téléphone","télévision","trait","trompette","voix","xylophone","zéro","ami","attention","camarade","colère","copain",
"coquin","dame","directeur","directrice","droit","effort","élève","enfant","fatigue","faute","fille","garçon","gardien","madame","maître","maîtresse","mensonge","ordre","personne","retard",
"sourire","travail","blond","brun","calme","curieux","différent","doux","énervé","gentil","grand","handicapé","inséparable","jaloux","moyen","muet","noir","nouveau","petit","poli","propre",
"roux","sage","sale","sérieux","sourd","tranquille","arrosoir","assiette","balle","bateau","boîte","bouchon","bouteille","bulles","canard","casserole","cuillère","cuvette","douche","entonnoir",
"gouttes","litre","moulin","pluie","poisson","pont","pot","roue","saladier","seau","tablier","tasse","trous","verre","amusant","chaud","froid","humide","intéressant","mouillé","sec","transparent",
"à l’endroit","à l’envers","anorak","arc","bagage","baguette","barbe","bonnet","botte","bouton","bretelle","cagoule","casque","casquette","ceinture","chapeau","chaussette","chausson","chaussure",
"chemise","cigarette","col","collant","couronne","cravate","culotte","écharpe","épée","fée","flèche","fusil","gant","habit","jean","jupe","lacet","laine","linge","lunettes","magicien","magie",
"maillot","manche","manteau","mouchoir","moufle","nœud","paire","pantalon","pied","poche","prince","pull-over","pyjama","reine","robe","roi","ruban","semelle","soldat","sorcière","tache","taille",
"talon","tissu","tricot","uniforme","valise","veste","vêtement","clair","court","étroit","foncé","joli","large","long","multicolore","nu","usé","aiguille","ampoule","avion","bois","bout",
"bricolage","bruit","cabane","carton","clou","colle","crochet","élastique","ficelle","fil","marionnette","marteau","métal","mètre","morceau","moteur","objet","outil","peinture","pinceau",
"planche","plâtre","scie","tournevis","vis","voiture","véhicule","adroit","difficile","dur","facile","lisse","maladroit","pointu","rugueux","tordu","accident","aéroport","auto","camion","engin",
"feu","frein","fusée","garage","gare","grue","hélicoptère","moto","panne","parking","pilote","pneu","quai","train","virage","vitesse","voyage","wagon","zigzag","abîmé","ancien","blanc","bleu",
"cassé","cinq","dernier","deux","deuxième","dix","gris","gros","huit","jaune","même","neuf","pareil","premier","quatre","rouge","sept","seul","six","solide","trois","troisième","un","vert",
"acrobate","arrêt","arrière","barre","barreau","bord","bras","cerceau","chaises","cheville","chute","cœur","corde","corps","côté","cou","coude","cuisse","danger","doigts","dos","échasses",
"échelle","épaule","équipe","escabeau","fesse","filet","fond","genou","gymnastique","hanche","jambes","jeu","mains","milieu","montagne","mur d’escalade","muscle","numéro","ongle","parcours",
"pas","passerelle","pente","peur","pieds","plongeoir","poignet","poing","pont de singe","poutre d’équilibre","prises","rivière des crocodiles","roulade","saut","serpent","sport","suivant","tête",
"toboggan","tour","trampoline","tunnel","ventre","dangereux","épais","fort","gauche","groupé","immobile","rond","serré","souple","bagarre","balançoire","ballon","bande","bicyclette","bille",
"cadenas","cage à écureuil","cerf-volant","château","coup","cour","course","échasse","flaque","paix","pardon","partie","pédale","pelle","pompe","préau","raquette","rayon","récréation","sable",
"sifflet","signe","tas","tricycle","tuyau","vélo","filet","allumette","anniversaire","appétit","beurre","coquille","crêpes","croûte","dessert","envie","faim","fève","four","galette","gâteau",
"goût","invitation","langue","lèvres","liquide","louche","mie","moitié","moule","odeur","œuf","part","pâte","pâtisserie","recette","rouleau","sel","soif","tarte","tranche","yaourt","barbouillé",
"demi","égal","entier","gourmand","mauvais","meilleur","mince","bassine","cocotte","épluchure","légume","pomme de terre","rondelle","soupe","consommé","potage","cru","cuit","vide","arête","frite",
"gobelet","jambon","os","poulet","purée","radis","restaurant","sole","animal","bébés","bouche","cage","câlin","caresse","cochon d’Inde","foin","graines","hamster","lapin","maison","nez","œil",
"oreille","patte","toit","yeux","abandonné","enceinte","maigre","mort","né","vivant","légume","abeille","agneau","aile","âne","arbre","bain","barque","bassin","bébé","bec","bête","bœuf",
"botte de foin","boue","bouquet","bourgeon","branche","caillou","campagne","car","champ","chariot","chat","cheminée","cheval","chèvre","chien","cochon","colline","coq","coquelicot","crapaud",
"cygne","départ","dindon","escargot","étang","ferme","fermier","feuille","flamme","fleur","fontaine","fumée","grain","graine","grenouille","griffe","guêpe","herbe","hérisson","insecte","jardin",
"mare","marguerite","miel","morceau de pain","mouche","mouton","oie","oiseau","pierre","pigeon","plante","plume","poney","poule","poussin","prairie","rat","rivière","route","tortue","tracteur",
"tulipe","vache","vétérinaire","bizarre","énorme","immense","malade","nain","utile","aigle","animaux","aquarium","bêtes","cerf","chouette","cigogne","crocodile","dauphin","éléphant","girafe",
"hibou","hippopotame","kangourou","lion","loup","ours","panda","panthère","perroquet","phoque","renard","requin","rhinocéros","singe","tigre","zèbre","zoo","épingle","bâton","bêtise","bonhomme",
"bottes","canne","cauchemar","cri","danse","déguisement","dinosaure","drapeau","en argent","en or","en rang","fête","figure","géant","gens","grand-mère","grand-père","joie","joue","journaux",
"maquillage","masque","monsieur","moustache","ogre","princesse","rue","trottoir","content","drôle","effrayé","heureux","joyeux","prêt","riche","terrible","Noël","boule","cadeau","canne à pêche",
"chance","cube","guirlande","humeur","papillon","spectacle","surprise","trou","visage","électrique","âge","an","année","après-midi","calendrier","début","dimanche","été","étoile","fin",
"heure des mamans","heure","hiver","horloge","jeudi","jour","journée","lumière","lundi","lune","mardi","matin","mercredi","midi","minuit","minute","mois","moment","montre","nuit","ombre",
"pendule","retour","réveil","saison","samedi","semaine","soir","soleil","temps","univers","vacances","vendredi","aîné","jeune","lent","patient","rapide","sombre","vieux","air","arc-en-ciel",
"brouillard","ciel","éclair","flocon","goutte","hirondelle","luge","neige","nuage","orage","ouragan","parapluie","parasol","ski","tempête","thermomètre","tonnerre","traîneau","vent","déçu",
"triste","chaud","froid","pluvieux","nuageux","humide","gelé","instable","changeant","assiette","balai","biscuit","boisson","bol","bonbon","céréale","confiture","coquetier","couteau","couvercle",
"couvert","cuillère","cuisine","cuisinière","désordre","dînette","éponge","évier","four","fourchette","lait","lave-linge","lessive","machine","nappe","pain","pile","plat","plateau","poêle",
"réfrigérateur","repas","tartine","torchon","vaisselle","bon","creux","délicieux","argent","aspirateur","bague","barrette","bijou","bracelet","brosse","cadre","canapé","chambre","cheveu","chiffon",
"cil","coffre","coffret","collier","couette","coussin","couverture","dent","dentifrice","drap","fauteuil","fer à repasser","frange","glace","lampe","lit","ménage","or","oreiller","parfum","peigne",
"pouf","poupée","poussette","poussière","shampoing","sourcil","trésor","tube","vase","beau","belle","confortable","coquet","douillet","adulte","album","amour","baiser","bavoir","biberon","bisou",
"caprice","cimetière","cousin","cousine","crèche","fils","frère","grand-parent","homme","femme","jumeau","maman","mari","mariage","mère","papa","parent","père","petit-enfant","petit-fils",
"petite-fille","rasoir","sœur","ambulance","bosse","champignon","dentiste","docteur","fièvre","front","gorge","infirmier","infirmière","jambe","larme","médecin","menton","mine","ordonnance",
"pansement","peau","piqûre","poison","sang","santé","squelette","trousse","guéri","pâle","araignée","brouette","chenille","coccinelle","fourmi","herbe","jonquille","lézard","pâquerette","rangée",
"râteau","rosé","souris","taupe","terrain","terre","terrier","tige","ver","mûr","profond","portière","sac","billet","caisse","farce","grimace","grotte","pays","regard","ticket","cruel","bûche",
"buisson","camp","chasseur","châtaigne","chemin","chêne","corbeau","écorce","écureuil","forêt","gourde","lac","loupe","lutin","marron","mûre","moustique","muguet","nid","paysage","pin","rocher",
"sapin","sommet","tente","adresse","appartement","ascenseur","balcon","boucherie","boulanger","boulangerie","boutique","bus","caniveau","caravane","carrefour","cave","charcuterie","cinéma",
"cirque","clin d’œil","cloche","clocher","clown","coiffeur","colis-route","courrier","croix","église","embouteillage","endroit","enveloppe","essence","facteur","fleuriste","foire","hôpital",
"hôtel","immeuble","incendie","laisse","magasin","manège","médicament","moineau","monde","monument","ouvrier","palais","panneau","paquet","parc","passage","pharmacie","pharmacien","piscine",
"place","police","policier","pompier","poste","promenade","quartier","square","timbre","travaux","usine","village","ville","voisin","volet","important","impossible","prudent","abricot","ail",
"aliment","ananas","banane","bifteck","café","carotte","cerise","chocolat","chou","citron","citrouille","clémentine","concombre","coquillage","corbeille","crabe","crevette","endive","farine",
"fraise","framboise","fromage","fruit","gâteau","haricot","huile","légume","marchand","melon","monnaie","navet","noisette","noix","nourriture","oignon","orange","panier","pâtes","pêche","persil",
"petit pois","poire","poireau","pomme","pomme de terre","prix","prune","queue","raisin","riz","salade","sucre","thé","tomate","viande","vin","cher","léger","lourd","plein","baleine","bouée","île",
"jumelles","marin","mer","mouette","navire","pêcheur","plage","poisson","port","sardine","serviette","vague","voile"]



def extraction(request) :
	for terme_a_ext in LIST_TERMES_A_EXTRAIRE :
		nbTermes = 0
		i = existTerme(terme_a_ext)
		if(i > -1) :
			nbTermes +=1
	return render(request,'chatbot/extraction.html',{'nbTermes': nbTermes})

