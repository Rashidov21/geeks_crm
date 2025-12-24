from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone
from .models import Lead, LeadStatus, FollowUp
from accounts.models import Branch
from courses.models import Course

User = get_user_model()


class LeadCRUDTestCase(TestCase):
    """Test CRUD operations for Lead model"""
    
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
        
        # Create sales user
        self.sales = User.objects.create_user(
            username='sales',
            password='sales123',
            role='sales',
            email='sales@test.com'
        )
        
        # Create regular user (no permissions)
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            role='student',
            email='user@test.com'
        )
        
        # Create lead status
        self.status = LeadStatus.objects.create(
            name='Yangi',
            code='new',
            order=1,
            color='#3B82F6',
            is_active=True
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
        
        # Create test lead
        self.lead = Lead.objects.create(
            name='Test Lead',
            phone='+998901234567',
            source='instagram',
            status=self.status,
            branch=self.branch,
            interested_course=self.course,
            created_by=self.admin
        )
    
    def test_lead_list_view(self):
        """Test lead list view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('crm:lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lead')
        self.assertIn('can_create', response.context)
        self.assertIn('can_edit', response.context)
        self.assertIn('can_delete', response.context)
    
    def test_lead_detail_view(self):
        """Test lead detail view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('crm:lead_detail', kwargs={'pk': self.lead.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lead')
    
    def test_lead_create_view_get(self):
        """Test lead create view GET request"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('crm:lead_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_lead_create_view_post(self):
        """Test lead create view POST request"""
        self.client.login(username='admin', password='admin123')
        data = {
            'name': 'New Lead',
            'phone': '+998901234568',
            'secondary_phone': '',
            'interested_course': self.course.pk,
            'source': 'telegram',
            'branch': self.branch.pk,
            'notes': 'Test notes'
        }
        response = self.client.post(reverse('crm:lead_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Lead.objects.filter(name='New Lead').exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('muvaffaqiyatli yaratildi' in str(m) for m in messages))
    
    def test_lead_edit_view_get(self):
        """Test lead edit view GET request"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('crm:lead_edit', kwargs={'pk': self.lead.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lead')
    
    def test_lead_update_view_post(self):
        """Test lead update view POST request"""
        self.client.login(username='admin', password='admin123')
        
        # Create new status for update
        updated_status = LeadStatus.objects.create(
            name='Aloqa qilindi',
            code='contacted',
            order=2,
            color='#10B981',
            is_active=True
        )
        
        data = {
            'name': 'Updated Lead',
            'phone': '+998901234569',
            'secondary_phone': '',
            'interested_course': self.course.pk,
            'source': 'youtube',
            'status': updated_status.pk,
            'branch': self.branch.pk,
            'notes': 'Updated notes'
        }
        response = self.client.post(
            reverse('crm:lead_edit', kwargs={'pk': self.lead.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Check lead was updated
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.name, 'Updated Lead')
        self.assertEqual(self.lead.status, updated_status)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('muvaffaqiyatli yangilandi' in str(m) for m in messages))
    
    def test_lead_delete_view_get(self):
        """Test lead delete confirmation view"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('crm:lead_delete', kwargs={'pk': self.lead.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lead')
    
    def test_lead_delete_view_post(self):
        """Test lead delete view POST request"""
        self.client.login(username='admin', password='admin123')
        lead_id = self.lead.pk
        response = self.client.post(reverse('crm:lead_delete', kwargs={'pk': lead_id}))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Check lead was deleted
        self.assertFalse(Lead.objects.filter(pk=lead_id).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('o\'chirildi' in str(m) for m in messages))
    
    def test_lead_permissions(self):
        """Test that permissions are correctly enforced"""
        # Regular user should not be able to create
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('crm:lead_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Sales user should be able to create
        self.client.login(username='sales', password='sales123')
        response = self.client.get(reverse('crm:lead_create'))
        self.assertEqual(response.status_code, 200)
        
        # Sales user should be able to edit their own leads
        self.lead.assigned_sales = self.sales
        self.lead.save()
        response = self.client.get(reverse('crm:lead_edit', kwargs={'pk': self.lead.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Sales user should not be able to delete
        response = self.client.post(reverse('crm:lead_delete', kwargs={'pk': self.lead.pk}))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Manager should be able to perform all CRUD operations
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('crm:lead_create'))
        self.assertEqual(response.status_code, 200)


class FollowUpCRUDTestCase(TestCase):
    """Test CRUD operations for FollowUp model"""
    
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
        
        # Create sales user
        self.sales = User.objects.create_user(
            username='sales',
            password='sales123',
            role='sales',
            email='sales@test.com'
        )
        
        # Create lead status
        self.status = LeadStatus.objects.create(
            name='Yangi',
            code='new',
            order=1,
            color='#3B82F6',
            is_active=True
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
        
        # Create lead
        self.lead = Lead.objects.create(
            name='Test Lead',
            phone='+998901234567',
            source='instagram',
            status=self.status,
            branch=self.branch,
            interested_course=self.course,
            created_by=self.admin
        )
        
        # Create follow-up
        self.followup = FollowUp.objects.create(
            lead=self.lead,
            sales=self.sales,
            due_date=timezone.now() + timezone.timedelta(days=1),
            notes='Test follow-up',
            completed=False
        )
    
    def test_followup_list_view(self):
        """Test follow-up list view loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('crm:followup_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('can_create', response.context)
        self.assertIn('can_edit', response.context)
    
    def test_followup_create_view(self):
        """Test follow-up create view"""
        self.client.login(username='sales', password='sales123')
        response = self.client.get(reverse('crm:followup_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_followup_update_view(self):
        """Test follow-up update view"""
        self.client.login(username='sales', password='sales123')
        data = {
            'due_date': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'notes': 'Updated notes',
            'completed': False
        }
        response = self.client.post(
            reverse('crm:followup_edit', kwargs={'pk': self.followup.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Check follow-up was updated
        self.followup.refresh_from_db()
        self.assertEqual(self.followup.notes, 'Updated notes')
    
    def test_followup_complete_view(self):
        """Test follow-up complete view"""
        self.client.login(username='sales', password='sales123')
        response = self.client.post(
            reverse('crm:followup_complete', kwargs={'pk': self.followup.pk}),
            {'next': 'crm:followup_today'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after completion
        
        # Check follow-up was completed
        self.followup.refresh_from_db()
        self.assertTrue(self.followup.completed)
        self.assertIsNotNone(self.followup.completed_at)
