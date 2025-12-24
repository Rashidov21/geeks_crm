from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import Course, Module, Topic, Group
from accounts.models import Branch

User = get_user_model()


class CourseCRUDTestCase(TestCase):
    """Test CRUD operations for Course model"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create branch
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='Test Address',
            phone='+998901234567'
        )
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin',
            email='admin@test.com'
        )
        
        # Create manager user
        self.manager = User.objects.create_user(
            username='manager',
            password='manager123',
            role='manager',
            email='manager@test.com'
        )
        
        # Create regular user (no permissions)
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            role='student',
            email='user@test.com'
        )
        
        # Create test course
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            branch=self.branch,
            duration_weeks=12,
            price=1000000.00,
            is_active=True
        )
    
    def test_course_list_view(self):
        """Test course list view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertIn('can_create', response.context)
        self.assertIn('can_edit', response.context)
        self.assertIn('can_delete', response.context)
    
    def test_course_detail_view(self):
        """Test course detail view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:course_detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertIn('can_edit', response.context)
    
    def test_course_create_view_get(self):
        """Test course create view GET request"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:course_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_course_create_view_post(self):
        """Test course create view POST request"""
        self.client.login(username='admin', password='admin123')
        data = {
            'name': 'New Course',
            'description': 'New Description',
            'branch': self.branch.pk,
            'duration_weeks': 16,
            'price': 2000000.00
        }
        response = self.client.post(reverse('courses:course_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Course.objects.filter(name='New Course').exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('muvaffaqiyatli yaratildi' in str(m) for m in messages))
    
    def test_course_edit_view_get(self):
        """Test course edit view GET request"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:course_edit', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertIn('is_edit', response.context)
    
    def test_course_update_view_post(self):
        """Test course update view POST request"""
        self.client.login(username='admin', password='admin123')
        data = {
            'name': 'Updated Course',
            'description': 'Updated Description',
            'branch': self.branch.pk,
            'duration_weeks': 20,
            'price': 3000000.00,
            'is_active': True
        }
        response = self.client.post(
            reverse('courses:course_edit', kwargs={'pk': self.course.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Check course was updated
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Updated Course')
        self.assertEqual(self.course.duration_weeks, 20)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('muvaffaqiyatli yangilandi' in str(m) for m in messages))
    
    def test_course_delete_view_get(self):
        """Test course delete confirmation view"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:course_delete', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
    
    def test_course_delete_view_post(self):
        """Test course delete view POST request"""
        self.client.login(username='admin', password='admin123')
        course_id = self.course.pk
        response = self.client.post(reverse('courses:course_delete', kwargs={'pk': course_id}))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Check course was deleted
        self.assertFalse(Course.objects.filter(pk=course_id).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('o\'chirildi' in str(m) for m in messages))
    
    def test_course_permissions(self):
        """Test that permissions are correctly enforced"""
        # Regular user should not be able to create
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('courses:course_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Regular user should not be able to edit
        response = self.client.get(reverse('courses:course_edit', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Regular user should not be able to delete
        response = self.client.post(reverse('courses:course_delete', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Manager should be able to perform CRUD operations
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('courses:course_create'))
        self.assertEqual(response.status_code, 200)


class GroupCRUDTestCase(TestCase):
    """Test CRUD operations for Group model"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create branch
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='Test Address',
            phone='+998901234567'
        )
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='admin',
            email='admin@test.com'
        )
        
        # Create course
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            branch=self.branch,
            duration_weeks=12,
            price=1000000.00,
            is_active=True
        )
        
        # Create mentor
        self.mentor = User.objects.create_user(
            username='mentor',
            password='mentor123',
            role='mentor',
            email='mentor@test.com'
        )
        
        # Create group
        from courses.models import Room
        self.room = Room.objects.create(
            branch=self.branch,
            name='Test Room',
            capacity=20,
            is_active=True
        )
        
        self.group = Group.objects.create(
            name='Test Group',
            course=self.course,
            mentor=self.mentor,
            room=self.room,
            is_active=True
        )
    
    def test_group_list_view(self):
        """Test group list view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:group_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group')
    
    def test_group_detail_view(self):
        """Test group detail view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:group_detail', kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group')
    
    def test_group_create_view(self):
        """Test group create view"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:group_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_group_update_view(self):
        """Test group update view"""
        self.client.login(username='admin', password='admin123')
        data = {
            'name': 'Updated Group',
            'course': self.course.pk,
            'mentor': self.mentor.pk,
            'room': self.room.pk,
            'is_active': True
        }
        response = self.client.post(
            reverse('courses:group_edit', kwargs={'pk': self.group.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Check group was updated
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Updated Group')
    
    def test_group_delete_view(self):
        """Test group delete view"""
        self.client.login(username='admin', password='admin123')
        group_id = self.group.pk
        response = self.client.post(reverse('courses:group_delete', kwargs={'pk': group_id}))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Check group was deleted
        self.assertFalse(Group.objects.filter(pk=group_id).exists())
