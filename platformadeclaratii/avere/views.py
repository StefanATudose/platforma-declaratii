from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django import forms
from django.views.generic.edit import FormView
import logging
from .forms import FileFieldForm
from .document_upload import DocumentUploadToDatabase
from .forms import IndividForm, ClasamentForm
from sqlalchemy import text
import matplotlib.pyplot as plt
from io import StringIO
import numpy as np

# class UploadFileForm(forms.Form):
#     files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


def menu(request):
    form = FileFieldForm
    return render(request, 'meniu.html', {'form': form})

class FileFormView(FormView):
    form_class = FileFieldForm
    template_name = "meniu.html" 
    success_url = "/upload_result" 
    #logger = logging.getLogger("mylogger")


    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        
        engine = DocumentUploadToDatabase.engine
        with engine.connect() as connection:
            titular_id, doc_id = DocumentUploadToDatabase.get_current_ids(connection)
            tipuri_doc = []
            
            for f in files:
                path = write_to_media(f, doc_id)
                tip_doc = DocumentUploadToDatabase.database_insertion(path, connection, titular_id, doc_id)
                tipuri_doc.append(tip_doc)
                titular_id += 1
                doc_id += 1

        return upload_result(self.request, tipuri_doc)
        # response = super().form_valid(form)
        # response.context_data = self.get_context_data()
        # response.context_data['tipuri_doc'] = tipuri_doc
        # return response

def upload_result(request, tipuri_doc_list):
    counts = {i: 0 for i in range(4)}
    logger = logging.getLogger("mylogger")
    for key, string in tipuri_doc_list:
        counts[key] += 1
    logger.info(tipuri_doc_list)
    logger.info(counts)        
    total = counts[0] + counts[1] + counts[2] + counts[3]

    return render(request, 'upload_result.html', {'total': total, 'tipuri_doc': counts, 'tipuri_doc_list': tipuri_doc_list})

def write_to_media(f, doc_id):
    with open(f'media/{doc_id}.pdf', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return f'media/{doc_id}.pdf'

def vezi_declaratii(request):
    form = IndividForm
    return render(request, "vezi_declaratii.html", {'form': form})

def rezultate_generale(request):
    logger = logging.getLogger("mylogger")
    
    if request.method == "POST":
        form = IndividForm(request.POST)
        if form.is_valid():
            nume = form.cleaned_data["nume"]
            query_list = []
            if nume:
                query = f"LOWER(nume) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{nume}%')"
                query_list.append(query)
            init_tata = form.cleaned_data["init_tata"]
            if init_tata:
                query = f"LOWER(init_tata) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{init_tata}%')"
                query_list.append(query)
            prenume = form.cleaned_data["prenume"]
            if prenume:
                query = f"LOWER(prenume) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{prenume}%')"
                query_list.append(query)
            functie = form.cleaned_data["functie"]
            if functie:
                query = f"LOWER(functie) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{functie}%')"
                query_list.append(query)
            institutie = form.cleaned_data["institutie"]
            if institutie:
                query = f"LOWER(institutie) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{institutie}%')"
                query_list.append(query)
            query_list = " and ".join(query_list)
            query_list = f"select * from titular where {query_list};"
            engine = DocumentUploadToDatabase.engine
            with engine.connect() as connection:
                lista_indivizi = connection.execute(text(query_list))
                lista_indivizi = [r for r in lista_indivizi]

            form = IndividForm(initial={'nume': nume, "init_tata": init_tata, 'prenume': prenume, 
                                        "functie": functie, 'institutie': institutie})

            return render(request, "rezultate_generale.html", 
            {'lista_indivizi': lista_indivizi, 'nume': nume, "init_tata": init_tata,
            'prenume': prenume, "functie": functie, 'institutie': institutie, 'form': form})
        
    return HttpResponseRedirect("/vezideclaratii")


def profil_individ(request, titular_id):
    engine = DocumentUploadToDatabase.engine
    with engine.connect() as connection:
        individ = connection.execute(text(f"select * from titular where titular_id = '{titular_id}'")).first()
        ani_avere = connection.execute(text(
        f"""select YEAR(data) from titular t join document d
        on t.titular_id = d.titular_id where d.tip_doc = '1' and t.titular_id = '{titular_id}' order by data asc;"""))
        ani_interese = connection.execute(text(
        f"""select YEAR(data) from titular t join document d
        on t.titular_id = d.titular_id where d.tip_doc = '2' and t.titular_id = '{titular_id}' order by data asc;"""))

    return render(request, "profil_individ.html", {'nume': individ.nume, "init_tata": individ.init_tata, 'an_ultima_avere' : individ.an_ultima_declaratie,
                                                    'prenume': individ.prenume, "functie": individ.functie,
                                                    'institutie': individ.institutie, 'avere_personala': individ.avere_personala, 'ani_avere': ani_avere,
                                                    'ani_interese': ani_interese, 'titular_id': titular_id})

def get_year_data(request, titular_id, year, doc_type):
    logger = logging.getLogger("mylogger")
    engine = DocumentUploadToDatabase.engine
    totalData = {}
         
    with engine.connect() as connection:
        doc = connection.execute(text(
        f"""select * from titular t 
            join document d
            on t.titular_id = d.titular_id where t.titular_id = '{titular_id}'
            and YEAR(d.data) = '{year}' and d.tip_doc = '{doc_type}';""")).first()._asdict()
        doc_id = doc["doc_id"]
        
        if doc_type == 1: 
            teren_cladire = connection.execute(text(
            f"""select * from TEREN_CLADIRE 
                where doc_id = '{doc_id}';"""))

            teren_cladire = [elem for elem in teren_cladire]
            teren = [elem._asdict() for elem in teren_cladire if elem.tip == 0]
            cladire = [elem._asdict() for elem in teren_cladire if elem.tip == 1]
            
            MIJLOC_TRANSPORT = connection.execute(text(
            f"""select * from MIJLOC_TRANSPORT 
                where doc_id = '{doc_id}';"""))
            MIJLOC_TRANSPORT = [elem._asdict() for elem in MIJLOC_TRANSPORT]
            
            BUN_CULTURAL = connection.execute(text(
            f"""select * from BUN_CULTURAL 
                where doc_id = '{doc_id}';"""))
            BUN_CULTURAL = [elem._asdict() for elem in BUN_CULTURAL]

            BUN_INSTRAINAT = connection.execute(text(
            f"""select * from BUN_INSTRAINAT 
                where doc_id = '{doc_id}';"""))
            BUN_INSTRAINAT = [elem._asdict() for elem in BUN_INSTRAINAT]

            ACTIVA_FINANCIARA_INDIRECTA = connection.execute(text(
            f"""select * from ACTIVA_FINANCIARA_INDIRECTA 
                where doc_id = '{doc_id}';"""))
            ACTIVA_FINANCIARA_INDIRECTA = [elem._asdict() for elem in ACTIVA_FINANCIARA_INDIRECTA]

            ACTIVA_FINANCIARA_DIRECTA = connection.execute(text(
            f"""select * from ACTIVA_FINANCIARA_DIRECTA 
                where doc_id = '{doc_id}';"""))
            ACTIVA_FINANCIARA_DIRECTA = [elem._asdict() for elem in ACTIVA_FINANCIARA_DIRECTA]

            ALTA_ACTIVA_FINANCIARA = connection.execute(text(
            f"""select * from ALTA_ACTIVA_FINANCIARA 
                where doc_id = '{doc_id}';"""))
            ALTA_ACTIVA_FINANCIARA = [elem._asdict() for elem in ALTA_ACTIVA_FINANCIARA]

            DATORIE = connection.execute(text(
            f"""select * from DATORIE 
                where doc_id = '{doc_id}';"""))
            DATORIE = [elem._asdict() for elem in DATORIE]

            AJUTOR = connection.execute(text(
            f"""select * from AJUTOR 
                where doc_id = '{doc_id}';"""))
            AJUTOR = [elem._asdict() for elem in AJUTOR]

            VENIT = connection.execute(text(
            f"""select * from VENIT 
                where doc_id = '{doc_id}';"""))
            VENIT = [elem._asdict() for elem in VENIT]
        

            totalData = {'doc': doc, 'teren': teren, 'cladire': cladire, 'mijloc_transport': MIJLOC_TRANSPORT,
                'bun_cultural': BUN_CULTURAL, 'bun_instrainat': BUN_INSTRAINAT, 
                'activa_financiara_indirecta': ACTIVA_FINANCIARA_INDIRECTA, 'activa_financiara_directa' : ACTIVA_FINANCIARA_DIRECTA,
                'alta_activa_financiara': ALTA_ACTIVA_FINANCIARA, 'datorie': DATORIE, 'ajutor': AJUTOR, 'venit': VENIT}
        else:
            MEMBRU_NON_STAT = connection.execute(text(
            f"""select * from MEMBRU_NON_STAT 
                where doc_id = '{doc_id}';"""))
            MEMBRU_NON_STAT = [elem._asdict() for elem in MEMBRU_NON_STAT]

            MEMBRU_STAT = connection.execute(text(
            f"""select * from MEMBRU_STAT 
                where doc_id = '{doc_id}';"""))
            MEMBRU_STAT = [elem._asdict() for elem in MEMBRU_STAT]

            MEMBRU_SINDICAT = connection.execute(text(
            f"""select * from MEMBRU_SINDICAT 
                where doc_id = '{doc_id}';"""))
            MEMBRU_SINDICAT = [elem._asdict() for elem in MEMBRU_SINDICAT]

            MEMBRU_PARTID = connection.execute(text(
            f"""select * from MEMBRU_PARTID 
                where doc_id = '{doc_id}';"""))
            MEMBRU_PARTID = [elem._asdict() for elem in MEMBRU_PARTID]

            CONTRACT = connection.execute(text(
            f"""select * from CONTRACT 
                where doc_id = '{doc_id}';"""))
            CONTRACT = [elem._asdict() for elem in CONTRACT]
            
            totalData = {'doc': doc, 'membru_non_stat': MEMBRU_NON_STAT, 'membru_stat': MEMBRU_STAT, 'membru_sindicat': MEMBRU_SINDICAT,
                'membru_partid': MEMBRU_PARTID, 'contract': CONTRACT}

    logger.info(totalData)
    return JsonResponse({'data': totalData })

def get_graphs(request, titular_id):
    engine = DocumentUploadToDatabase.engine
    logger = logging.getLogger("mylogger")
    with engine.connect() as connection:
        docs = connection.execute(text(
            f"""select * from document d where d.titular_id = {titular_id} and d.tip_doc = '1';"""))
        teren_cladire = connection.execute(text(
            f"""select * from TEREN_CLADIRE tc
                join document d
                on tc.doc_id = d.doc_id
                where d.titular_id = {titular_id} order by d.data asc;"""))
        
        teren_cladire = [elem for elem in teren_cladire]
        teren = [elem._asdict() for elem in teren_cladire if elem.tip == 0]
        cladire = [elem._asdict() for elem in teren_cladire if elem.tip == 1]


        MIJLOC_TRANSPORT = connection.execute(text(
        f"""select * from MIJLOC_TRANSPORT mt
            join document d
            on mt.doc_id = d.doc_id
            where d.titular_id = '{titular_id}' order by d.data asc;"""))
        
        MIJLOC_TRANSPORT = [elem._asdict() for elem in MIJLOC_TRANSPORT]

        bun_cultural = connection.execute(text(
            f"""select * from BUN_CULTURAL bc
                join document d
                on bc.doc_id = d.doc_id
                where d.titular_id = '{titular_id}' order by d.data asc;"""
        ))
        bun_cultural = [elem._asdict() for elem in bun_cultural]

        activa_financiara_indirecta = connection.execute(text(
            f"""select * from ACTIVA_FINANCIARA_INDIRECTA afi
                join document d
                on afi.doc_id = d.doc_id
                where d.titular_id = '{titular_id}' order by d.data asc;"""
        ))
        activa_financiara_indirecta = [elem._asdict() for elem in activa_financiara_indirecta]

        activa_financiara_directa = connection.execute(text(
            f"""select * from ACTIVA_FINANCIARA_DIRECTA afd
                join document d
                on afd.doc_id = d.doc_id
                where d.titular_id = '{titular_id}' order by d.data asc;"""
        ))
        activa_financiara_directa = [elem._asdict() for elem in activa_financiara_directa]

        alta_activa_financiara = connection.execute(text(
            f"""select * from ALTA_ACTIVA_FINANCIARA aaf
                join document d
                on aaf.doc_id = d.doc_id
                where d.titular_id = '{titular_id}' order by d.data asc;"""
        ))
        alta_activa_financiara = [elem._asdict() for elem in alta_activa_financiara]

        datorie = connection.execute(text(
            f"""select * from DATORIE da
                join document d
                on da.doc_id = d.doc_id
                where d.titular_id = '{titular_id}' order by d.data asc;"""
        ))
        datorie = [elem._asdict() for elem in datorie]

    docs = [doc._asdict() for doc in docs]
    averi = [doc["avere_doc"] for doc in docs]
    years = [int(str(doc["data"])[:4]) for doc in docs]
    fig = plt.figure()
    plt.plot(years, averi)
    plt.xlabel('Ani')
    plt.xticks(years)
    plt.ylabel('Euro')
    plt.yticks(averi)
    plt.title('Avere_personala')

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    graf_avere = imgdata.getvalue()

    graf_terenuri_nr = get_plot_number_per_years(teren, 'Terenuri', 'Numar terenuri')
    graf_cladiri_nr = get_plot_number_per_years(cladire, 'Cladiri', 'Numar cladiri')
    graf_teren_mp2 = get_mp2_teren_cladire_per_year(teren, 'mp2', 'Suprafata terenuri')
    graf_cladire_mp2 = get_mp2_teren_cladire_per_year(cladire, 'mp2', 'Suprafata cladiri')
    graf_MIJLOC_TRANSPORT_nr = get_plot_number_per_years(MIJLOC_TRANSPORT, 'Automobile', 'Numar_terenuri')
    graf_bun_cultural_nr = get_plot_number_per_years(bun_cultural, 'Bunuri culturale', 'Numar bunuri culturale')
    graf_activa_financiara_indirecta_nr = get_plot_number_per_years(activa_financiara_indirecta, 'Active', 'Numar active financiare indirecte')
    graf_activa_financiara_directa_nr = get_plot_number_per_years(activa_financiara_directa, 'Active', 'Numar active financiare directe')
    graf_alta_activa_financiara_nr = get_plot_number_per_years(alta_activa_financiara, 'Active', 'Numar alte active financiare')
    graf_datorie_nr = get_plot_number_per_years(datorie, 'Datorii', 'Numar datorii')


    return JsonResponse({'graf_avere': graf_avere, 'graf_terenuri_nr': graf_terenuri_nr, 'graf_cladiri_nr': graf_cladiri_nr, 'graf_teren_mp2': graf_teren_mp2, 'graf_cladire_mp2': graf_cladire_mp2, 
                        'graf_MIJLOC_TRANSPORT_nr': graf_MIJLOC_TRANSPORT_nr, 'graf_bun_cultural_nr': graf_bun_cultural_nr,
                        'graf_activa_financiara_indirecta_nr': graf_activa_financiara_indirecta_nr, 'graf_activa_financiara_directa_nr': graf_activa_financiara_directa_nr,
                        'graf_alta_activa_financiara_nr': graf_alta_activa_financiara_nr, "graf_datorie_nr": graf_datorie_nr})

def get_mp2_teren_cladire_per_year(data, ce_plotez, titlu):
    teren_per_ani = {}
    for elem in data:
        curr = int(str(elem["data"])[:4])
        if curr not in teren_per_ani:
            teren_per_ani[curr] = elem['suprafata']
        else:
            teren_per_ani[curr] += elem['suprafata']
    
    lists = sorted(teren_per_ani.items()) 

    x, y = zip(*lists)

    fig = plt.figure()
    plt.plot(x, y)
    plt.xlabel('Ani')
    plt.ylabel(ce_plotez)
    plt.xticks(x)
    plt.yticks(y)
    plt.title(titlu)

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    return imgdata.getvalue()

def get_plot_number_per_years(data, ce_plotez, titlu):
    teren_per_ani = {}
    for elem in data:
        curr = int(str(elem["data"])[:4])
        if curr not in teren_per_ani:
            teren_per_ani[curr] = 1
        else:
            teren_per_ani[curr] += 1

    
    lists = sorted(teren_per_ani.items()) 
    if not lists:
            return 
    x, y = zip(*lists)

    fig = plt.figure()
    plt.plot(x, y)
    plt.xlabel('Ani')
    plt.ylabel(ce_plotez)
    plt.xticks(x)
    plt.yticks(y)
    plt.title(titlu)

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    return imgdata.getvalue()
    
def clasament_search(request):
    form = ClasamentForm
    return render(request, "clasament_search.html", {'form': form})


def clasament_results(request):
    if request.method == "POST":
        form = ClasamentForm(request.POST)
        if form.is_valid():
            functie = form.cleaned_data["functie"]
            query_list = [f"avere_personala != -1 "]
            if functie:
                query = f"LOWER(functie) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{functie}%')"
                query_list.append(query)

            institutie = form.cleaned_data["institutie"]
            if institutie:
                query = f"LOWER(institutie) COLLATE utf8mb4_unicode_520_ci LIKE LOWER('%{institutie}%')"
                query_list.append(query)
            
            query_list = 'where ' + " and ".join(query_list)

            query_list = f"select * from titular {query_list} order by avere_personala desc;"
            engine = DocumentUploadToDatabase.engine
            with engine.connect() as connection:
                lista_indivizi = connection.execute(text(query_list))
                lista_indivizi = [r for r in lista_indivizi]
            if len(lista_indivizi) > 100:
                lista_indivizi = lista_indivizi[:100]
            return render(request, "clasament_results.html", {'lista_indivizi': lista_indivizi,
            "functie": functie, 'institutie': institutie})
        
    return HttpResponseRedirect("/clasament_search")
    # path("clasament_results", views.clasament_results, name="clasament_results"),