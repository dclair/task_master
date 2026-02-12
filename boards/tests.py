from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Board, BoardMembership


# En esta suite valido permisos mínimos del CRUD de tableros para evitar regresiones.
class BoardCrudPermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Preparo cuatro perfiles para cubrir owner/editor/viewer y usuario externo.
        cls.owner = User.objects.create_user(username="owner", password="pass12345")
        cls.editor = User.objects.create_user(username="editor", password="pass12345")
        cls.viewer = User.objects.create_user(username="viewer", password="pass12345")
        cls.outsider = User.objects.create_user(username="outsider", password="pass12345")

        # Creo un tablero base y asigno membresias con rol para probar permisos.
        cls.board = Board.objects.create(
            title="Tablero Inicial",
            description="Descripcion inicial",
            owner=cls.owner,
        )
        BoardMembership.objects.create(board=cls.board, user=cls.owner, role="owner")
        BoardMembership.objects.create(board=cls.board, user=cls.editor, role="editor")
        BoardMembership.objects.create(board=cls.board, user=cls.viewer, role="viewer")

    def test_owner_can_open_board_edit_page(self):
        self.client.login(username="owner", password="pass12345")
        response = self.client.get(reverse("boards:board_edit", args=[self.board.pk]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_edit_board(self):
        self.client.login(username="owner", password="pass12345")
        response = self.client.post(
            reverse("boards:board_edit", args=[self.board.pk]),
            data={"title": "Tablero Editado", "description": "Nueva descripcion"},
        )
        self.assertRedirects(response, reverse("boards:board_list"))
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, "Tablero Editado")
        self.assertEqual(self.board.description, "Nueva descripcion")

    def test_editor_cannot_edit_board(self):
        self.client.login(username="editor", password="pass12345")
        response = self.client.get(reverse("boards:board_edit", args=[self.board.pk]))
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_edit_board(self):
        self.client.login(username="viewer", password="pass12345")
        response = self.client.get(reverse("boards:board_edit", args=[self.board.pk]))
        self.assertEqual(response.status_code, 403)

    def test_non_member_cannot_edit_board(self):
        self.client.login(username="outsider", password="pass12345")
        response = self.client.get(reverse("boards:board_edit", args=[self.board.pk]))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_from_board_edit(self):
        response = self.client.get(reverse("boards:board_edit", args=[self.board.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_owner_can_delete_board(self):
        self.client.login(username="owner", password="pass12345")
        response = self.client.post(reverse("boards:board_delete", args=[self.board.pk]))
        self.assertRedirects(response, reverse("boards:board_list"))
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())

    def test_editor_cannot_delete_board(self):
        self.client.login(username="editor", password="pass12345")
        response = self.client.post(reverse("boards:board_delete", args=[self.board.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())

    def test_viewer_cannot_delete_board(self):
        self.client.login(username="viewer", password="pass12345")
        response = self.client.post(reverse("boards:board_delete", args=[self.board.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())

    def test_anonymous_redirected_from_board_delete(self):
        response = self.client.post(reverse("boards:board_delete", args=[self.board.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())
