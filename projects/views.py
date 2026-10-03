from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import roles_required
from accounts.decorators import permission_required
from .models import Project, ProjectFile, ProjectUpdate
from .forms import ProjectForm, ProjectFileForm, ProjectUpdateForm


@login_required
@permission_required('projects.view')
def project_list(request):
    """List all public projects - accessible to all members"""
    # All authenticated users can see public projects
    projects = Project.objects.filter(is_public=True).order_by('-created_at')
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        projects = projects.filter(category=category)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        projects = projects.filter(status=status)
    
    context = {
        'projects': projects,
        'categories': Project.CATEGORY_CHOICES,
        'statuses': [
            ('planning', 'Planning'),
            ('active', 'Active Development'),
            ('completed', 'Completed'),
            ('archived', 'Archived'),
        ]
    }
    return render(request, 'projects/project_list.html', context)


@login_required
@permission_required('projects.view')
def project_detail(request, project_id):
    """View project details - members can view all resources and code
    
    All authenticated members can view:
    - Project description and information
    - All code files with syntax highlighting
    - All uploaded assets
    - Project updates and progress
    - Team members
    
    Only project members can add files/updates
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is a project member or creator
    is_member = request.user.is_authenticated and (
        request.user in project.members.all() or 
        request.user == project.created_by
    )
    
    files = project.files.all()
    updates = project.updates.all()
    
    context = {
        'project': project,
        'files': files,
        'updates': updates,
        'is_member': is_member,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
@roles_required(['president', 'vp_events', 'assistant_event'])
def create_project(request):
    """Create a new project"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            project.members.add(request.user)  # Add creator as member
            messages.success(request, f'Project "{project.title}" created successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    context = {'form': form}
    return render(request, 'projects/create_project.html', context)


@login_required
@permission_required('projects.edit')
def edit_project(request, project_id):
    """Edit an existing project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permission
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    context = {'form': form, 'project': project}
    return render(request, 'projects/edit_project.html', context)


@login_required
@permission_required('projects.delete')
def delete_project(request, project_id):
    """Delete a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permission
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('project_list')
    
    context = {'project': project}
    return render(request, 'projects/delete_project.html', context)


@login_required
@permission_required('projects.edit')
def add_file(request, project_id):
    """Add a code file or asset to project
    
    Only project members and creator can add files
    Regular members cannot add but can VIEW all files
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is project member or creator
    if request.method == 'POST':
        form = ProjectFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.project = project
            file_obj.uploaded_by = request.user
            file_obj.save()
            messages.success(request, f'File "{file_obj.title}" added successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectFileForm()
    
    context = {'form': form, 'project': project}
    return render(request, 'projects/add_file.html', context)


@login_required
@permission_required('projects.delete')
def delete_file(request, file_id):
    """Delete a file from project"""
    file_obj = get_object_or_404(ProjectFile, id=file_id)
    project = file_obj.project
    
    if request.method == 'POST':
        file_obj.delete()
        messages.success(request, 'File deleted successfully!')
        return redirect('project_detail', project_id=project.id)
    
    context = {'file': file_obj}
    return render(request, 'projects/delete_file.html', context)


@login_required
@permission_required('projects.edit')
def add_update(request, project_id):
    """Add a progress update to project
    
    Only project members and creator can post updates
    Regular members can VIEW all updates but cannot post
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is project member or creator
    if request.method == 'POST':
        form = ProjectUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.project = project
            update.author = request.user
            update.save()
            messages.success(request, 'Update posted successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectUpdateForm()
    
    context = {'form': form, 'project': project}
    return render(request, 'projects/add_update.html', context)
