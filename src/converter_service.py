from utils import read_json
from dcat_ap import dcat_ap

class converterService(object):

    def __init__(self, catalog_title, catalog_uri, input_path,  out_path):
        self.data = read_json(input_path)
        self.catalog_title = catalog_title
        self.catalog_uri = catalog_uri
        self.out_path = out_path
        self.convert()


    def convert(self):
        dcat_ap_ins = dcat_ap()
        # data_item = self.data["0"]['publication']['oai_dc:dc']
        dcat_ap_ins.add_catalog(self.data, self.catalog_uri, self.catalog_title )
        dcat_ap_ins.save_graph(self.out_path)


if __name__ == '__main__':
    service = converterService("HU  Berlin EDOC", "https://edoc.hu-berlin.de/", "hu-edoc.json","hu_berlin_catalog.rdf")