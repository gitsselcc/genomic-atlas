import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_data import load_data,validate,valid_date,valid_url
class DataTests(unittest.TestCase):
    def setUp(self):self.data=load_data()
    def test_catalog(self):self.assertEqual(validate(self.data),[])
    def test_urls(self):
        self.assertTrue(valid_url('https://example.org/program'))
        self.assertFalse(valid_url('javascript:alert(1)'))
        self.assertFalse(valid_url('http://example.org'))
    def test_dates(self):
        self.assertTrue(valid_date('2027-04-24'))
        self.assertFalse(valid_date('2027-02-30'))
    def test_duplicate_area(self):
        data=copy.deepcopy(self.data);data['areas'].append(copy.deepcopy(data['areas'][0]))
        self.assertTrue(any('duplicado' in e for e in validate(data)))
    def test_unverified_cannot_be_marked_verified_without_date(self):
        data=copy.deepcopy(self.data)
        data['institutions']=[{'id':'demo','name':'Demo','country':'México','website':'https://example.org'}]
        data['opportunities']=[{'id':'demo','title':'Demo','description':'Demo','type':'summer','institution_id':'demo','research_area_ids':[data['areas'][0]['id']],'level':['undergraduate'],'official_url':'https://example.org','verification_status':'verified'}]
        self.assertTrue(any('last_verified' in e for e in validate(data)))
if __name__=='__main__':unittest.main()
