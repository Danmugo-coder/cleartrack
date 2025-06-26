from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from clearance.models import Student, ClearanceForm, ClearanceField, ApprovalSignature
from django.utils import timezone
import uuid

# Create your views here.

def home(request):
    """
    Home page view that redirects to the appropriate dashboard based on user type
    """
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            if request.user.profile.user_type == 'admin' or request.user.is_superuser:
                return redirect('dashboard:admin_dashboard')
            elif request.user.profile.user_type == 'user':
                return redirect('dashboard:user_dashboard')
            else:
                return redirect('dashboard:staff_dashboard')
    return render(request, 'core/home.html')

def scan_clearance(request):
    """
    View for scanning QR code to view clearance form without login
    """
    # Process form submission (manual token entry)
    if request.method == 'POST':
        token = request.POST.get('token')
        if token:
            try:
                # Try parse UUID
                token_uuid = uuid.UUID(token)
                # Verify the student exists
                student = get_object_or_404(Student, token=token_uuid)
                return redirect('core:view_clearance', token=token_uuid)
            except (ValueError, Student.DoesNotExist):
                messages.error(request, 'Invalid token format or student not found. Please try again.')
                return redirect('core:home')
    return redirect('core:home')

def view_clearance(request, token):
    """
    View for displaying a student's clearance form without login
    """
    try:
        # Ensure a valid UUID
        token_uuid = uuid.UUID(str(token))
        student = get_object_or_404(Student, token=token_uuid)
        
        try:
            clearance_form = ClearanceForm.objects.get(student=student)
            
            # Get all fields
            all_fields = clearance_form.fields.all()
            
            # Find landlord/landlady fields
            landlord_fields = all_fields.filter(
                Q(name__icontains='landlord') | Q(name__icontains='landlady')
            )
            
            # Get non-landlord fields
            non_landlord_fields = all_fields.exclude(
                Q(name__icontains='landlord') | Q(name__icontains='landlady')
            )
            
            # Calculate correct total fields
            total_fields = non_landlord_fields.count()
            if landlord_fields.exists():
                total_fields += 1 
            
            # Calculate signed fields (for landlord fields, count as signed if any one is signed)
            signed_fields = non_landlord_fields.filter(status=True).count()
            if landlord_fields.filter(status=True).exists():
                signed_fields += 1
            
            if total_fields > 0:
                progress_percentage = int((signed_fields / total_fields) * 100)
            else:
                progress_percentage = 0
            
            # Add calculated values to clearance_form
            clearance_form.total_fields = total_fields
            clearance_form.signed_fields = signed_fields
            clearance_form.progress_percentage = progress_percentage
            
            # Get approval signatures
            try:
                approval_dean = ApprovalSignature.objects.get(form=clearance_form, role='dean')
            except ApprovalSignature.DoesNotExist:
                approval_dean = None
            
            try:
                approval_registrar = ApprovalSignature.objects.get(form=clearance_form, role='registrar')
            except ApprovalSignature.DoesNotExist:
                approval_registrar = None
            
        except ClearanceForm.DoesNotExist:
            messages.error(request, "This student does not have a clearance form yet.")
            return redirect('core:home')
        
        context = {
            'student': student,
            'clearance_form': clearance_form,
            'approval_dean': approval_dean,
            'approval_registrar': approval_registrar,
        }
        
        return render(request, 'core/view_clearance.html', context)
        
    except (ValueError, TypeError, Student.DoesNotExist):
        messages.error(request, "Invalid student token or student not found.")
        return redirect('core:home')
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

