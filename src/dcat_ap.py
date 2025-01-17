from rdflib import Graph, URIRef, BNode, Literal, Namespace

xMetaDiss = "xMetaDiss:xMetaDiss"
OAI_DC = "oai_dc:dc"
from matches import get_matches
class dcat_ap(object):

    def __init__(self, outpath):
        """
        Dcat-ap converter
        """
        self.graph = Graph()
        self.DCAT = Namespace('http://www.w3.org/ns/dcat#')
        self.DCTERMS = Namespace('http://purl.org/dc/terms/')
        self.FOAF = Namespace('http://xmlns.com/foaf/0.1/')
        self.RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.dcatde = Namespace('http://dcat-ap.de/def/dcatde/')
        self.XSD = Namespace('http://www.w3.org/2001/XMLSchema#')
        self.VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
        self.LOCN = Namespace('http://www.w3.org/ns/locn#')
        self.graph.bind('foaf', self.FOAF)
        self.graph.bind('dct', self.DCTERMS)
        self.graph.bind('dcat', self.DCAT)
        self.graph.bind('dcatde', self.dcatde)
        self.graph.bind('rdf', self.RDF)
        self.graph.bind('xsd', self.XSD)
        self.graph.bind('vcard', self.VCARD)
        self.graph.bind('locn', self.LOCN)
        self.out_path = outpath
        

    def add_dataset(self, data, catalog_uri, llm_matches, elements_path, terms_path):
        """ add dataset to graph"""
        # print(data)
        dataset_uri = BNode()
        self.graph.add((dataset_uri, self.RDF.type, self.DCAT.Dataset))
        self.graph.add((catalog_uri, self.DCAT.Dataset, dataset_uri))
        #get matches from experiments
        matches = get_matches(data, llm_matches, elements_path, terms_path)
        self.functions = {}

        def func_not_found(data, dataset_uri):
           pass
        for name in matches.values():
            self.functions[name]="add_"+name

        # print(matches)

        for meta in data.keys():
            if not meta.startswith("@"):
                if meta in matches.keys():
                    function_name = matches[meta] 
                    # print(function_name)
                    func = self.functions[function_name]
                    func = getattr(self, func, func_not_found) 
                    # print(func)
                    func(data, dataset_uri)
     
    

    def add_catalog(self, dataset, catalog_uri_text, catalog_title, llm_matches, elements_path, terms_path):
        """ add catalog to graph"""

        catalog_uri = URIRef(catalog_uri_text)
        title = catalog_title
        self.graph.add((catalog_uri, self.RDF.type, self.DCAT.Catalog))
        self.graph.add((catalog_uri, self.DCTERMS.title, Literal(title)))
        len_ = len(dataset)
        # create RDF for

        for i in range(0,len_):

            item = None
            key = None

            for key in dataset[str(i)].keys():
                item = dataset[str(i)][key]
                if key == xMetaDiss:
                    break
                if  key == OAI_DC:
                    item = item[key]
                    break

            if key == OAI_DC:
                item = item[key]
                
            if item is not None:
                self.add_dataset(item, catalog_uri, llm_matches, elements_path, terms_path)
            

        self.save_graph(self.out_path  + ".rdf")

              
    def add_title(self, data, dataset_uri):
        """ add title to dataset
        """
        # print(data)
        if type(data['dc:title']) is list:
            
            for title in data['dc:title']:
                if type(title) is dict:
                    title = title['#text']
                    self.graph.add(( dataset_uri, self.DCTERMS.title, Literal(title)))
                else:
                    self.graph.add((dataset_uri, self.DCTERMS.title, Literal(title)))
        elif type(data['dc:title']) is dict:
            title = data['dc:title']['#text']
            self.graph.add((dataset_uri, self.DCTERMS.title, Literal(title)))
        else:
            title = data['dc:title']
            self.graph.add((dataset_uri, self.DCTERMS.title, Literal(title)))

    def add_person(self, person_uri, creator, dataset_uri):

        self.graph.add((person_uri, self.RDF.type, self.FOAF.Person))
        self.graph.add((person_uri, self.FOAF.name, Literal(creator)))
        self.graph.add((dataset_uri, self.DCTERMS.creator, person_uri))

    def add_creator(self, data, dataset_uri):
        """ add creator to graph"""
        person_uri = BNode()
        if type(data['dc:creator']) is list:
            for creator in data['dc:creator']:
                if type(creator) is dict:
                    if "#text" in creator.keys():
                        creator = creator["pc:person"]['pc:name']['pc:foreName']+" "+creator['#text']["pc:person"]['pc:name']['pc:surName']
                        self.add_person(person_uri, creator, dataset_uri)
                else:
                    self.add_person(person_uri, creator, dataset_uri)
        elif type(data['dc:creator']) is dict:
            if "#text" in data['dc:creator'].keys():
                creator = data['dc:creator'] = data['dc:creator']["pc:person"]['pc:name']['pc:foreName']+" "+data['dc:creator']["pc:person"]['pc:name']['pc:surName']
                self.add_person(person_uri, creator, dataset_uri)
        else:
            creator = data['dc:creator']
            self.add_person(person_uri, creator, dataset_uri)
        

    
    def add_subject(self, data, dataset_uri):
        """add subject to graph
        """

        if type(data['dc:subject']) is list:

            for subject in data['dc:subject']:
    
                if type(subject) is dict and "#text" in subject.keys():
                    if subject['@xsi:type'] == 'xMetaDiss:noScheme':
                        if subject['#text'] != "{'@xsi:type': 'xMetaDiss:noScheme'}":
                            subject = self.normalize_subject(subject['#text'])
                            self.graph.add((dataset_uri, self.DCAT.keyword, Literal(subject)))

                elif "ddc:" not in subject:
                    if type(subject) is str and subject != "{'@xsi:type': 'xMetaDiss:noScheme'}":
                        subject = self.normalize_subject(subject)
                        self.graph.add((dataset_uri, self.DCAT.keyword, Literal(subject)))

        elif type(data['dc:subject']) is dict and "#text" in data['dc:subject'].keys():
            if data['dc:subject']['@xsi:type'] == 'xMetaDiss:noScheme':
                if data['dc:subject']['#text'] != "{'@xsi:type': 'xMetaDiss:noScheme'}":
                    subject = self.normalize_subject = data['dc:subject']['#text']
                    self.graph.add((dataset_uri, self.DCAT.keyword, Literal(subject)))
        else:
            if data['dc:subject'] != "{'@xsi:type': 'xMetaDiss:noScheme'}":
                subject = self.normalize_subject(data['dc:subject'])
                self.graph.add((dataset_uri, self.DCAT.keyword, Literal(subject)))

    def add_abstract(self, data, dataset_uri):
        """abstract to graph
        """
        if "dcterms:abstract" in data.keys():
            if type(data["dcterms:abstract"]) is list:
                for abstract in data["dcterms:abstract"]:
                    if "#text" in abstract.keys():
                        description = abstract['#text']
                        self.graph.add((dataset_uri, self.DCTERMS.description, Literal(description)))
            elif type(data["dcterms:abstract"]) is dict and "#text" in data["dcterms:abstract"].keys():
                description = data["dcterms:abstract"]["#text"]
                self.graph.add((dataset_uri, self.DCTERMS.description, Literal(description)))
    
    def add_description(self, data, dataset_uri): 
        if 'dc:description' in data.keys():  
            if type(data['dc:description']) is list:
                for description in data['dc:description']:
                    self.graph.add((dataset_uri, self.DCTERMS.description, Literal(description)))
            elif type(data['dc:description']) is dict:
                description = data['dc:description']['#text']
                self.graph.add((dataset_uri, self.DCTERMS.description, Literal(description)))
            else:
                description = data['dc:description']
                self.graph.add((dataset_uri, self.DCTERMS.description, Literal(description)))

    def add_issued(self, data, dataset_uri):
        """add date to graph
        """
        if 'dc:date' in data.keys():
            if type(data['dc:date']) is list:
                self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(data['dc:date'][0])))
                self.add_modified(data['dc:date'][1], dataset_uri)

            elif type(data['dc:date']) is dict:
                self.add_issued(data['dc:date']['#text'], dataset_uri)
                self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(data['dc:date']['#text'])))
            else:
                self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(data['dc:date'])))

        if 'dcterms:created' in data.keys():
            if type(data['dcterms:created']) is list:
                for created in data['dcterms:created']:
                    if type(created) is dict:
                        date = created['#text']
                        self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(date)))
                    else:
                        self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(date)))
            elif type(data['dcterms:created']) is dict:
                date = data['dcterms:created']['#text']
                self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(date)))
            else:
                date = data['dcterms:created']
                self.graph.add((dataset_uri, self.DCTERMS.issued, Literal(date)))
    
    def add_modified(self, data, dataset_uri):
        """add date to graph
        """
        if type(data["dcterms:dateSubmitted"]) is list:
            for date in data["dcterms:dateSubmitted"]:
                if type(date) is dict:
                    date = date['#text']
                    self.graph.add((dataset_uri, self.DCTERMS.modified, Literal(date)))
                else:
                    self.graph.add((dataset_uri, self.DCTERMS.modified, Literal(date)))
        elif type(data["dcterms:dateSubmitted"]) is dict:
            date = data["dcterms:dateSubmitted"]['#text']
            self.graph.add((dataset_uri, self.DCTERMS.modified, Literal(date)))
        else:
            date = data["dcterms:dateSubmitted"]
            self.graph.add((dataset_uri, self.DCTERMS.modified, Literal(date)))

    def add_type(self, data, dataset_uri):
        """add type to graph"""

        if type(data['dc:type']) is list:
            for _type_ in data['dc:type']:
                self.graph.add((dataset_uri, self.DCTERMS.type, Literal(_type_)))
        elif type(data['dc:type']) is dict:
            _type_ = data['dc:type']['#text']
            self.graph.add((dataset_uri, self.DCTERMS.type, Literal(_type_)))
        else:
            _type_ = data['dc:type']
            self.graph.add((dataset_uri, self.DCTERMS.type, Literal(_type_)))

    def add_format(self, data, dataset_uri):
        """add format to graph"""
        if type(data['dc:format']) is list:
            for format_ in data['dc:format']:
                self.graph.add((dataset_uri, self.DCTERMS.Format, Literal(format_)))
        elif type(data['dc:format']) is dict:
                format = data['dc:format']['#text']
                self.graph.add((dataset_uri, self.DCTERMS.Format, Literal(format)))
        else:
            format = data['dc:format'], dataset_uri
            self.graph.add((dataset_uri, self.DCTERMS.Format, Literal(format)))

    def add_rights(self, data, dataset_uri):
        """add rights to graph"""
        if type(data['dc:rights']) is list:
            for rights in data['dc:rights']:
                self.graph.add((dataset_uri, self.DCTERMS.rights, Literal(rights)))
        elif type(data['dc:rights']) is dict:
            self.graph.add((dataset_uri, self.DCTERMS.rights, Literal(data['dc:rights']['#text'])))
        else:
            self.graph.add((dataset_uri, self.DCTERMS.rights, Literal(data['dc:rights'])))

    def add_language(self, data, dataset_uri):
        """add language to graph"""
        if type(data['dc:language']) is list:

            for language in data['dc:language']:
                self.graph.add((dataset_uri, self.DCTERMS.language, Literal(language)))
        elif type(data['dc:language']) is dict:
            language = data['dc:language']['#text']
            self.graph.add((dataset_uri, self.DCTERMS.language, Literal(language)))
        else: 
            language = data['dc:language']
            self.graph.add((dataset_uri, self.DCTERMS.language, Literal(language)))
        

    def add_identifier(self, data, dataset_uri):
        """add identifier to graph"""
        if 'dc:identifier' in data.keys():
            if type(data['dc:identifier']) is list:
                for identifier in data['dc:identifier']:
                    self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))
            elif type(data['dc:identifier']) is dict:
                identifier = data['dc:identifier']['#text']
                self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))
            else:
                identifier = data['dc:identifier']
                self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))
        if 'ddb:identifier' in data.keys():
            if type(data['ddb:identifier']) is list:
            
                for identifier in data['ddb:identifier']:
                    if type(identifier) is dict and "#text" in identifier.keys():
                        identifier = identifier['#text']
                        self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))
                    else:
                        self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))

            elif type(data['ddb:identifier']) is dict and '#text' in data['ddb:identifier']:
                identifier = data['ddb:identifier']['#text']
                self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))
            else:
                identifier = data['ddb:identifier']
                self.graph.add((dataset_uri, self.DCTERMS.identifier, Literal(identifier)))

    def save_graph(self, filepath):
        """save graph to file"""
        self.graph.serialize(destination=filepath, format='pretty-xml')

    def normalize_subject(self, subject):
        """convert subject to lower case and remove special characters
        Args:
            subject (str): keywords about the dataset
        return:
            str: the lower case version of the subject.
        """
        return str(subject).lower().replace("_", " ").replace("-", " ")
    
