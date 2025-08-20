import unittest
from src.parsers.ricos_schema import heading, paragraph, image_node_wix_media, text_node

class TestRicosIdGeneration(unittest.TestCase):

    def test_id_in_heading_node(self):
        """Verifica se o nó de cabeçalho contém um ID único."""
        node = heading(1, [text_node("Meu Cabeçalho")])
        self.assertIn("id", node)
        self.assertTrue(isinstance(node["id"], str))
        self.assertGreater(len(node["id"]), 0)

    def test_id_in_paragraph_node(self):
        """Verifica se o nó de parágrafo contém um ID único."""
        node = paragraph([text_node("Meu parágrafo.")])
        self.assertIn("id", node)
        self.assertTrue(isinstance(node["id"], str))
        self.assertGreater(len(node["id"]), 0)

    def test_id_in_image_node(self):
        """Verifica se o nó de imagem contém um ID único."""
        media_id = "wix:image://v1/12345/image.jpg#originWidth=1920&originHeight=1080"
        image_data = {
            "media": {
                "src": {
                    "url": media_id,
                    "_id": media_id
                },
                "width": 1920,
                "height": 1080
            }
        }
        node = image_node_wix_media(media_id, None)
        self.assertIn("id", node)
        self.assertTrue(isinstance(node["id"], str))
        self.assertGreater(len(node["id"]), 0)

    def test_ids_are_unique(self):
        """Verifica se os IDs gerados são únicos."""
        node1 = paragraph([text_node("Primeiro parágrafo")])
        node2 = paragraph([text_node("Segundo parágrafo")])
        self.assertNotEqual(node1.get("id"), node2.get("id"))

if __name__ == '__main__':
    unittest.main()