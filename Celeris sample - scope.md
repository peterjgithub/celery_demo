Celeris sample - scope

Maak een eenvoudig basis django demo app die via RabbitMQ taken door een celery laat uitvoeren.

zorg dat de werking van Celery Groups en Chords aangetoond wordt

Taken orkestreren (Task Chaining):
Dummy Task dummy A.
Dummy Task B
Dummy Task C

toon de werking van een chord aan met een paar voorbeelden
maak ook enkele chords die onvolledig blijven (header niet klaar)
ik wil die in flower kunnen zien
voorzie een functie om onvolledige chords te kunnen afsluiten (deleten) met een on_failure handeling
en om een onvolledige chord te kunnen laten starten zodat die de onderliggende taken toch begint uit te voeren.

Zorg dat er een paar celery tasks zijn die nieuwe tasks aanmaken (eenmalig, geen eeuwigdurende herhalingen)

als een Celery Workflow nog een andere betekenis heeft, voeg dan een voorbeeld toe (sla over als dit hetzelfde is)

+ zorg ook dat er 1 extra scheduled task bij zit

Zorg dat elke celery taak een log-record aanmaakt in een centrale Audit Trail

Monitoring met flower
- Real-time Monitoring: Progress Tracking
- sample Timeout
- Task Details & Foutopsporing
- Remote Control: Termineren, Auto-refresh

Deploy in mijn docker (Infrastucture as code)