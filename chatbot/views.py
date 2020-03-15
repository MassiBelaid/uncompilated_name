from django.shortcuts import render
from django.http import HttpResponse
from datetime import date
from chatbot.models import Terme,Relation
import re

NON_FORT = -10
NON_FAIBLE = -2
SAIS_PAS = 5
OUI_FAIBLE = 30



def home(request):
	today = date.today()
	phrase = request.GET.get('phrase') or ''
	if(phrase == '') :
		return render(request,'chatbot/chatbot.html',{'date':today})
	else :
		reponse = traitement_phrase(phrase)
		return render(request,'chatbot/chatbot.html',{'date':today,'reponse':reponse})



def view_date(request, jour, mois, annee=2020):
	return render (request,'chatbot/date.html',locals())










def existTerme(ter) :
    b = False
    listTermes = Terme.objects.all()
    for elt in listTermes :
        if(elt.terme == ter) :
            b = True
    return b 


def searchRelation(termeU1,relation_recherchee,termeU2) :
	find = False
	listRelations = Relation.objects.filter(relation = relation_recherchee)
	for rel in listRelations :
		if (termeU1 == rel.terme1.terme and termeU2 == rel.terme2.terme ):
			find = True
			if (rel.poids < NON_FORT):
				return "absolument pas"
			elif(rel.poids < NON_FAIBLE):
				return "plutot non"
			elif(rel.poids < SAIS_PAS) :
				return "Je ne sais pas"
			elif(rel.poids < OUI_FAIBLE) :
				return"globalement"
			else :
				return "oui absolument"
	if(find == False) :
		for rel in listRelations :
			if(termeU1 == rel.terme1.terme and relation_recherchee == rel.relation) :
				p1 = rel.poids
				for rel2 in listRelations :
					if(rel.terme2.terme == rel2.terme1.terme and relation_recherchee == rel2.relation and termeU2 == rel2.terme2.terme) :
						p2 = rel2.poids
						if(p1 >= OUI_FAIBLE and p2 >= OUI_FAIBLE) :
							return "sûrement"
							poids = OUI_FAIBLE
							find = True
						elif((p1 < OUI_FAIBLE and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < OUI_FAIBLE)) :
							if((p1 >= SAIS_PAS and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= SAIS_PAS)) :
								return "probablement"
								poids = SAIS_PAS
								find = True
							elif((p1 >= NON_FAIBLE and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FAIBLE)) :
								return "Aucune idée"
								poids = 0
								find = True
							elif((p1 >= NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FORT)) :
								return "j'en doute"
								poids = -3
								find = True
							elif((p1 < NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < NON_FORT)) :
								return "Impossible"
								poids = -11
								find = True
		if(find) :
			listRelations.append(r)
            #print(listRelations)
		else :
			if(relation_recherchee == "has_part"):
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.terme, relation = "has_part", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								return "obligé"
							elif(r.poids >= SAIS_PAS) :
								return "plutot oui"
							else :
								return "je ne sais pas"
					else :
						return "je ne sais pas"
				return "has_part"
			else:	
				return "Je ne sais pas"

def searchRelationPourquoi(termeU1,relation_recherchee,termeU2) :
	find = False
	listRelations = Relation.objects.filter(relation = relation_recherchee)
	for rel in listRelations :
		if (termeU1 == rel.terme1.terme and termeU2 == rel.terme2.terme ):
			find = True
			if (rel.poids < NON_FORT):
				return "absolument pas"
			elif(rel.poids < NON_FAIBLE):
				return "plutot non"
			elif(rel.poids < SAIS_PAS) :
				return "Je ne sais pas"
			elif(rel.poids < OUI_FAIBLE) :
				return"globalement"
			else :
				return "oui absolument"
	if(find == False) :
		for rel in listRelations :
			if(termeU1 == rel.terme1.terme and relation_recherchee == rel.relation) :
				p1 = rel.poids
				for rel2 in listRelations :
					if(rel.terme2.terme == rel2.terme1.terme and relation_recherchee == rel2.relation and termeU2 == rel2.terme2.terme) :
						p2 = rel2.poids
						if(p1 >= OUI_FAIBLE and p2 >= OUI_FAIBLE) :
							termeC1 = termeU1
							termeC2 = rel.terme2.terme
							termeC3 = termeU2
							if(relation_recherchee == "is_a") :
								reponse = "peut être parce que {} est sous-classe de {}, qui est sous-classe de {} ".format(termeC3,termeC2,termeC1)
							elif(relation_recherchee == "has_part") :
								reponse = "peut être parce que {} est composé de {}, qui composé de {} ".format(termeC3,termeC2,termeC1)
							elif(relation_recherchee == "has_attribute") :
								reponse = "peut être parce que {} peut avoir comme propriété {}, qui peut avoir comme propriété {} ".format(termeC3,termeC2,termeC1)

							return reponse
							poids = OUI_FAIBLE
							find = True
						elif((p1 < OUI_FAIBLE and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < OUI_FAIBLE)) :
							if((p1 >= SAIS_PAS and p2 >= OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= SAIS_PAS)) :
								return "Je ne suis pas certain de cela"
								poids = SAIS_PAS
								find = True
							elif((p1 >= NON_FAIBLE and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FAIBLE)) :
								return "Aucune idée"
								poids = 0
								find = True
							elif((p1 >= NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 >= NON_FORT)) :
								return "j'en doute que cela soit le cas"
								poids = -3
								find = True
							elif((p1 < NON_FORT and p2 >=OUI_FAIBLE) or (p1 >= OUI_FAIBLE and p2 < NON_FORT)) :
								return "Impossible, a mon avis c'est tout le contraire"
								poids = -11
								find = True
		if(find) :
			listRelations.append(r)
            #print(listRelations)
		else :
			if(relation_recherchee == "has_part"):
				list_relation_has_part = Relation.objects.filter(relation = "is_a",terme1 = termeU1)
				for rel in list_relation_has_part :
					relation = Relation.objects.filter(terme1 = rel.terme2.terme, relation = "has_part", terme2 = termeU2)
					if len(relation) > 0:
						for r in relation :
							if(r.poids >= OUI_FAIBLE) :
								termeC1 = termeU1
								termeC2 = rel.terme2.terme
								termeC3 = termeU2
								reponse = "peut être parce que {} est sous-classe de {}, qui est composé de {} ".format(termeC1,termeC2,termeC3)
								return reponse
							elif(r.poids >= SAIS_PAS) :
								return "pas sure !"
							else :
								return "je ne sais pas"
					else :
						return "je ne sais pas"
				return "has_part"
			else:	
				return "Je ne sais pas"

    #print("{} {} {} {}".format(r.terme1,r.relation,r.terme2,r.poids))

def traitement_phrase(message):
    message = message.lower()
    list = message.split()
    print(list)
    
    if(list[0] == "est-ce" and list[1][0] == "q" and list[1][1] == "u"):
        """ Question du style est-ce qu.......
                """
        
        if (list[2] == "un" or list[2] == "une") :
            """ phrase du style est-ce que un/une .........
                """
            i = 3
        else :
            """ phrase du style est-ce que/qu'une/qu'un .....
                """
            i = 2    

        compris = True
        if((list[i+1] == "est" and not(re.search(list[i+2], r"une?") is None) and len(list[i+2]) < 4 and list[i+3] == "sous-classe") or \
            (list[i+1] == "appartient" and list[i+2] == "à" and list[i+3] == "la" and list[i+4] == "classe")or \
            (list[i+1] == "est" and list[i+2] == "sous-classe")) :
            """ Question du style K est {une/un} sous-classe/appartient à la classe
                Relation is_a
                """

            if(list[i+1] == "est") :
                """Question formulée de la premiére façon
                    """
                j = i+5
                if (list[i+2] != "un" and list[i+2] != "une"):
                    """est sous-classe
                        """
                    j -= 1
            else :
                """Question formulée de la deuxiemme façon
                    """
                j = i+6
            if(list[j] == "une" or list[j] == "un") :
                j += 1    

            relation_recherchee = "is_a"            



        elif((list[i+1] == "est" and list[i+2] == "composé") or \
            (list[i+1] == "est" and not(re.search(list[i+2], r"une?") is None) and len(list[i+2]) < 4 and list[i+3] == "partie")) :
            """Question du style K est composé/ est une partie ......
                Relation has_part
                """
            if(list[i+2] == "composé") :
                """Question du style K est composé de....
                    """
                j = i+4
                if (list[j]=="un" or list[j]=="une"):
                    j += 1
            else :
                """Question du style K' est une partie de .....
                    """        
                j = i+5
                if (list[j]=="un" or list[j]=="une"):
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
                if(list[j] == "un" or list[j] == "une") :
                    j += 1
            relation_recherchee = "has-attribute"        


        else :
            """Question non comprise
                """
            return "Je ne comprend pas votre question"
            compris = False   
        
        if(compris) :
            print("Vous cherchez une relation {} {} {}".format(list[i],relation_recherchee,list[j]))
            #termeU1 = Terme(list[i])
            existeTerme1 = existTerme(list[i])
            if(existeTerme1) :
                #termeU2 = Terme(list[j])
                teU2 = list[j]
                if(teU2[len(teU2)-1] == '?'):
                	teU2 = teU2[0:len(teU2)-1]
                existeTerme2 = existTerme(teU2)
                if(existeTerme2) :
                    """On reconnait les deux termes que l'utilisateur à introduit
                    On cherche si la relation entre les deux existe """

                    print("Je connais les deux termes")
                    print(searchRelation(list[i],relation_recherchee,teU2))
                    return searchRelation(list[i],relation_recherchee,teU2)
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

        if((list[i] == "un") or (list[i] == "une")) :
        	i += 1   

        compris = True
        if((list[i+1] == "est" and not(re.search(list[i+2], r"une?") is None) and len(list[i+2]) < 4 and list[i+3] == "sous-classe") or \
            (list[i+1] == "appartient" and list[i+2] == "à" and list[i+3] == "la" and list[i+4] == "classe")or \
            (list[i+1] == "est" and list[i+2] == "sous-classe")) :
            """ Question du style K est {une/un} sous-classe/appartient à la classe
                Relation is_a
                """

            if(list[i+1] == "est") :
                """Question formulée de la premiére façon
                    """
                j = i+5
                if (list[i+2] != "un" and list[i+2] != "une"):
                    """est sous-classe
                        """
                    j -= 1
            else :
                """Question formulée de la deuxiemme façon
                    """
                j = i+6
            if(list[j] == "une" or list[j] == "un") :
                j += 1    

            relation_recherchee = "is_a"            



        elif((list[i+1] == "est" and list[i+2] == "composé") or \
            (list[i+1] == "est" and not(re.search(list[i+2], r"une?") is None) and len(list[i+2]) < 4 and list[i+3] == "partie")) :
            """Question du style K est composé/ est une partie ......
                Relation has_part
                """
            if(list[i+2] == "composé") :
                """Question du style K est composé de....
                    """
                j = i+4
                if (list[j]=="un" or list[j]=="une"):
                    j += 1
            else :
                """Question du style K' est une partie de .....
                    """        
                j = i+5
                if (list[j]=="un" or list[j]=="une"):
                    j += 1
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
                if(list[j] == "un" or list[j] == "une") :
                    j += 1
            relation_recherchee = "has-attribute"        


        else :
            """Question non comprise
                """
            return "Je ne comprend pas votre question"
            compris = False   
        
        if(compris) :
            print("Vous cherchez une relation {} {} {}".format(list[i],relation_recherchee,list[j]))
            #termeU1 = Terme(list[i])
            existeTerme1 = existTerme(list[i])
            if(existeTerme1) :
                #termeU2 = Terme(list[j])
                teU2 = list[j]
                if(teU2[len(teU2)-1] == '?'):
                	teU2 = teU2[0:len(teU2)-1]
                existeTerme2 = existTerme(teU2)
                if(existeTerme2) :
                    """On reconnait les deux termes que l'utilisateur à introduit
                    On cherche si la relation entre les deux existe """

                    print("Je connais les deux termes")
                    print(searchRelationPourquoi(list[i],relation_recherchee,teU2))
                    return searchRelationPourquoi(list[i],relation_recherchee,teU2)
                else :
                    """Le deuxiemme Terme est inconnu
                        """
                    return "Je ne connais pas ce qu'est {}".format(teU2)       
            else :
                """Le Premier Terme est inconnu
                    """
                return "Je ne connais pas ce qu'est {}".format(list[i])

    else:
        """Ceci n'est peut etre pas une question
            """
        return "{} est une question ? ".format(message)

