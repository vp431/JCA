from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'college_choice_filling_app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college_choice.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    branches = db.relationship('CollegeBranch', backref='college', lazy=True)

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class CollegeBranch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    cutoff_rank = db.Column(db.Integer)
    branch = db.relationship('Branch')
    
class ChoiceList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    creator = db.Column(db.String(100), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    choices = db.relationship('Choice', backref='choice_list', lazy=True)

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('choice_list.id'), nullable=False)
    college_branch_id = db.Column(db.Integer, db.ForeignKey('college_branch.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    college_branch = db.relationship('CollegeBranch')

# Default branches
DEFAULT_BRANCHES = ['CSE', 'MNC', 'AI', 'AI+DS', 'DC', 'EC', 'Electronics', 'Electrical']

# Routes
@app.route('/')
def index():
    main_list = ChoiceList.query.filter_by(is_main=True).first()
    return render_template('index.html', main_list=main_list)

@app.route('/colleges')
def colleges():
    all_colleges = College.query.all()
    return render_template('colleges.html', colleges=all_colleges)

@app.route('/add_college', methods=['GET', 'POST'])
def add_college():
    if request.method == 'POST':
        name = request.form['name']
        
        new_college = College(name=name)
        db.session.add(new_college)
        db.session.commit()
        
        flash('College added successfully!', 'success')
        return redirect(url_for('colleges'))
    
    return render_template('add_college.html')

@app.route('/add_college_branch', methods=['GET', 'POST'])
def add_college_branch():
    if request.method == 'POST':
        college_id = request.form['college_id']
        branch_name = request.form['branch_name']
        cutoff_rank_type = request.form.get('cutoff_rank_type', 'numeric')
        
        # Get or create branch
        branch = Branch.query.filter_by(name=branch_name).first()
        if not branch:
            branch = Branch(name=branch_name)
            db.session.add(branch)
            db.session.commit()
        
        # Check if college-branch combination already exists
        existing_cb = CollegeBranch.query.filter_by(
            college_id=college_id, branch_id=branch.id).first()
        
        if existing_cb:
            flash('This college-branch combination already exists!', 'danger')
        else:
            # Handle cutoff rank based on type
            if cutoff_rank_type == 'na':
                cutoff_rank = None
            else:
                cutoff_rank = request.form.get('cutoff_rank', type=int)
                if cutoff_rank is None:
                    cutoff_rank = 0
            
            new_cb = CollegeBranch(college_id=college_id, branch_id=branch.id, cutoff_rank=cutoff_rank)
            db.session.add(new_cb)
            db.session.commit()
            flash('College branch added successfully!', 'success')
        
        return redirect(url_for('colleges'))
    
    colleges = College.query.all()
    branches = Branch.query.all()
    default_branches = DEFAULT_BRANCHES
    
    return render_template('add_college_branch.html', 
                           colleges=colleges, 
                           branches=branches, 
                           default_branches=default_branches)

@app.route('/lists')
def lists():
    all_lists = ChoiceList.query.order_by(ChoiceList.created_at.desc()).all()
    return render_template('lists.html', lists=all_lists)

@app.route('/create_list', methods=['GET', 'POST'])
def create_list():
    if request.method == 'POST':
        name = request.form['name']
        creator = request.form['creator']
        is_main = 'is_main' in request.form
        
        # If this is set as main list, unset any existing main list
        if is_main:
            current_main = ChoiceList.query.filter_by(is_main=True).first()
            if current_main:
                current_main.is_main = False
                db.session.commit()
        
        new_list = ChoiceList(name=name, creator=creator, is_main=is_main)
        db.session.add(new_list)
        db.session.commit()
        
        flash('List created successfully!', 'success')
        return redirect(url_for('edit_list', list_id=new_list.id))
    
    return render_template('create_list.html')

@app.route('/edit_list/<int:list_id>', methods=['GET', 'POST'])
def edit_list(list_id):
    choice_list = ChoiceList.query.get_or_404(list_id)
    
    if request.method == 'POST':
        # Handle reordering or updates
        pass
    
    # Get current choices in the list
    choices = Choice.query.filter_by(list_id=list_id).order_by(Choice.position).all()
    college_branches = []
    
    # Track college-branch IDs already in the list
    existing_cb_ids = [choice.college_branch_id for choice in choices]
    
    for choice in choices:
        cb = choice.college_branch
        college = College.query.get(cb.college_id)
        branch = Branch.query.get(cb.branch_id)
        
        college_branches.append({
            'id': choice.id,
            'position': choice.position,
            'college_name': college.name,
            'branch_name': branch.name,
            'cutoff_rank': cb.cutoff_rank
        })
    
    # Get available college-branch combinations not already in the list
    available_college_branches = []
    all_college_branches = CollegeBranch.query.all()
    
    for cb in all_college_branches:
        if cb.id not in existing_cb_ids:
            college = College.query.get(cb.college_id)
            branch = Branch.query.get(cb.branch_id)
            
            available_college_branches.append({
                'id': cb.id,
                'college_name': college.name,
                'branch_name': branch.name,
                'cutoff_rank': cb.cutoff_rank
            })
    
    # Sort available options by college name and then branch name
    available_college_branches.sort(key=lambda x: (x['college_name'], x['branch_name']))
    
    return render_template('edit_list.html', 
                          list=choice_list, 
                          choices=college_branches,
                          available_college_branches=available_college_branches)

@app.route('/add_choice/<int:list_id>', methods=['POST'])
def add_choice(list_id):
    college_branch_id = request.form['college_branch_id']
    
    # Find the college branch
    cb = CollegeBranch.query.get_or_404(college_branch_id)
    
    # Check if this college-branch is already in the list
    existing_choice = Choice.query.filter_by(
        list_id=list_id, college_branch_id=college_branch_id).first()
    
    if existing_choice:
        flash('This college-branch combination is already in your list!', 'warning')
        return redirect(url_for('edit_list', list_id=list_id))
    
    # Get the highest position in the list
    highest_pos = db.session.query(db.func.max(Choice.position)).filter_by(list_id=list_id).scalar()
    if highest_pos is None:
        highest_pos = 0
    
    # Add the choice to the list
    new_choice = Choice(list_id=list_id, college_branch_id=cb.id, position=highest_pos + 1)
    db.session.add(new_choice)
    db.session.commit()
    
    flash('Choice added to list successfully!', 'success')
    return redirect(url_for('edit_list', list_id=list_id))

@app.route('/move_choice/<int:choice_id>/<direction>', methods=['POST'])
def move_choice(choice_id, direction):
    choice = Choice.query.get_or_404(choice_id)
    
    if direction == 'up' and choice.position > 1:
        # Find the choice above
        above_choice = Choice.query.filter_by(
            list_id=choice.list_id, position=choice.position - 1).first()
        
        if above_choice:
            # Swap positions
            above_choice.position, choice.position = choice.position, above_choice.position
            db.session.commit()
    
    elif direction == 'down':
        # Find the choice below
        below_choice = Choice.query.filter_by(
            list_id=choice.list_id, position=choice.position + 1).first()
        
        if below_choice:
            # Swap positions
            below_choice.position, choice.position = choice.position, below_choice.position
            db.session.commit()
    
    return redirect(url_for('edit_list', list_id=choice.list_id))

@app.route('/delete_choice/<int:choice_id>', methods=['POST'])
def delete_choice(choice_id):
    choice = Choice.query.get_or_404(choice_id)
    list_id = choice.list_id
    
    # Get all choices with higher positions
    higher_choices = Choice.query.filter(
        Choice.list_id == list_id,
        Choice.position > choice.position
    ).all()
    
    # Delete the choice
    db.session.delete(choice)
    
    # Update positions of remaining choices
    for c in higher_choices:
        c.position -= 1
    
    db.session.commit()
    
    flash('Choice removed from list!', 'success')
    return redirect(url_for('edit_list', list_id=list_id))

@app.route('/export_list/<int:list_id>/<format>', methods=['GET'])
def export_list(list_id, format):
    choice_list = ChoiceList.query.get_or_404(list_id)
    choices = Choice.query.filter_by(list_id=list_id).order_by(Choice.position).all()
    
    if format == 'txt':
        # Create TXT export
        txt_content = f"List: {choice_list.name}\nTentative JoSAA Counselling list for Dharmi\nCreated by: {choice_list.creator}\nDate: {choice_list.created_at.strftime('%Y-%m-%d')}\n\n"
        txt_content += "Sr. No | College | Branch | Cutoff Rank\n"
        txt_content += "-" * 80 + "\n"
        
        for i, choice in enumerate(choices, 1):
            cb = choice.college_branch
            college = College.query.get(cb.college_id)
            branch = Branch.query.get(cb.branch_id)
            
            cutoff_rank_display = "N/A" if cb.cutoff_rank is None else str(cb.cutoff_rank)
            txt_content += f"{i} | {college.name} | {branch.name} | {cutoff_rank_display}\n"
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        temp_file.write(txt_content.encode('utf-8'))
        temp_file.close()
        
        return send_file(temp_file.name, 
                        mimetype='text/plain',
                        as_attachment=True,
                        download_name=f"{choice_list.name.replace(' ', '_')}.txt")
    
    elif format == 'pdf':
        # Create PDF using reportlab instead of pdfkit
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.close()
        
        # Set up the PDF document
        doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create the elements for the PDF
        elements = []
        
        # Add title and metadata
        title_style = styles['Heading1']
        elements.append(Paragraph(f"{choice_list.name}", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Tentative JoSAA Counselling list for Dharmi", styles['Normal']))
        elements.append(Paragraph(f"Created by: {choice_list.creator}", styles['Normal']))
        elements.append(Paragraph(f"Date: {choice_list.created_at.strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Create data for the table
        data = [["Sr. No", "College", "Branch", "Cutoff Rank"]]
        
        for i, choice in enumerate(choices, 1):
            cb = choice.college_branch
            college = College.query.get(cb.college_id)
            branch = Branch.query.get(cb.branch_id)
            
            cutoff_rank_display = "N/A" if cb.cutoff_rank is None else str(cb.cutoff_rank)
            data.append([
                str(i),
                college.name,
                branch.name,
                cutoff_rank_display
            ])
        
        # Create the table
        table = Table(data)
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),  # Dark blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e3f2fd')),  # Light blue background
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#90caf9'))  # Medium blue grid
        ])
        
        # Add alternating row colors with different shades of blue
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#bbdefb'))  # Slightly darker blue for alternating rows
        
        table.setStyle(style)
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
        
        return send_file(temp_pdf.name,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=f"{choice_list.name.replace(' ', '_')}.pdf")

@app.route('/import_list', methods=['GET', 'POST'])
def import_list():
    if request.method == 'POST':
        if 'list_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['list_file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file:
            # Process the uploaded TXT file
            content = file.read().decode('utf-8')
            lines = content.strip().split('\n')
            
            # Parse header info
            list_name = lines[0].replace('List: ', '')
            creator = lines[1].replace('Created by: ', '')
            
            # Create a new list
            new_list = ChoiceList(name=list_name, creator=creator)
            db.session.add(new_list)
            db.session.commit()
            
            # Skip header lines and table header
            data_lines = lines[5:]
            position = 1
            
            for line in data_lines:
                parts = line.split('|')
                if len(parts) >= 4:  # Format: Sr. No | College | Branch | Cutoff Rank
                    college_name = parts[1].strip()
                    branch_name = parts[2].strip()
                    cutoff_rank = parts[3].strip()
                    
                    # Find or create college
                    college = College.query.filter_by(name=college_name).first()
                    if not college:
                        try:
                            college = College(name=college_name)
                            db.session.add(college)
                            db.session.commit()
                        except Exception as e:
                            flash(f'Error adding college {college_name}: {str(e)}', 'danger')
                            continue
                    
                    # Find or create branch
                    branch = Branch.query.filter_by(name=branch_name).first()
                    if not branch:
                        branch = Branch(name=branch_name)
                        db.session.add(branch)
                    
                    # Find or create college-branch
                    cb = CollegeBranch.query.filter_by(college_id=college.id, branch_id=branch.id).first()
                    if not cb:
                        try:
                            if cutoff_rank.strip().upper() == "N/A":
                                rank = None
                            else:
                                rank = int(cutoff_rank)
                        except ValueError:
                            rank = 0
                            
                        cb = CollegeBranch(college_id=college.id, branch_id=branch.id, cutoff_rank=rank)
                        db.session.add(cb)
                        db.session.commit()
                    
                    # Add choice to list
                    choice = Choice(list_id=new_list.id, college_branch_id=cb.id, position=position)
                    db.session.add(choice)
                    position += 1
            
            db.session.commit()
            flash('List imported successfully!', 'success')
            return redirect(url_for('edit_list', list_id=new_list.id))
    
    return render_template('import_list.html')

@app.route('/set_main_list/<int:list_id>', methods=['POST'])
def set_main_list(list_id):
    # Unset current main list
    current_main = ChoiceList.query.filter_by(is_main=True).first()
    if current_main:
        current_main.is_main = False
    
    # Set new main list
    new_main = ChoiceList.query.get_or_404(list_id)
    new_main.is_main = True
    
    db.session.commit()
    flash(f'"{new_main.name}" is now set as the main list', 'success')
    
    return redirect(url_for('lists'))

@app.route('/delete_list/<int:list_id>', methods=['POST'])
def delete_list(list_id):
    choice_list = ChoiceList.query.get_or_404(list_id)
    
    # Get list name for flash message
    list_name = choice_list.name
    was_main = choice_list.is_main
    
    # Delete all choices in the list first
    Choice.query.filter_by(list_id=list_id).delete()
    
    # Delete the list itself
    db.session.delete(choice_list)
    db.session.commit()
    
    if was_main:
        flash(f'Main list "{list_name}" has been deleted successfully. You may want to set a new main list.', 'warning')
    else:
        flash(f'List "{list_name}" has been deleted successfully', 'success')
    
    return redirect(url_for('lists'))

@app.route('/duplicate_list/<int:list_id>', methods=['POST'])
def duplicate_list(list_id):
    # Get the original list
    original_list = ChoiceList.query.get_or_404(list_id)
    
    # Create a new list with similar properties
    new_list = ChoiceList(
        name=f"Copy of {original_list.name}",
        creator=original_list.creator,
        is_main=False  # Never set a duplicated list as main
    )
    db.session.add(new_list)
    db.session.commit()
    
    # Get all choices from the original list
    original_choices = Choice.query.filter_by(list_id=original_list.id).order_by(Choice.position).all()
    
    # Duplicate each choice
    for choice in original_choices:
        new_choice = Choice(
            list_id=new_list.id,
            college_branch_id=choice.college_branch_id,
            position=choice.position
        )
        db.session.add(new_choice)
    
    db.session.commit()
    
    flash(f'List "{original_list.name}" has been duplicated successfully as "{new_list.name}"', 'success')
    return redirect(url_for('lists'))

@app.route('/update_list_name/<int:list_id>', methods=['POST'])
def update_list_name(list_id):
    choice_list = ChoiceList.query.get_or_404(list_id)
    new_name = request.form.get('list_name', '').strip()
    
    if not new_name:
        flash('List name cannot be empty', 'danger')
        return redirect(url_for('edit_list', list_id=list_id))
    
    # Update the list name
    old_name = choice_list.name
    choice_list.name = new_name
    db.session.commit()
    
    flash(f'List name updated from "{old_name}" to "{new_name}"', 'success')
    return redirect(url_for('edit_list', list_id=list_id))

@app.route('/api/colleges', methods=['GET'])
def api_colleges():
    colleges = College.query.all()
    result = []
    
    for college in colleges:
        branches = []
        
        for cb in college.branches:
            branch = Branch.query.get(cb.branch_id)
            branches.append({
                'id': branch.id,
                'name': branch.name,
                'cutoff_rank': cb.cutoff_rank
            })
        
        result.append({
            'id': college.id,
            'name': college.name,
            'branches': branches
        })
    
    return jsonify(result)

@app.route('/api/branches', methods=['GET'])
def api_branches():
    branches = Branch.query.all()
    result = [{
        'id': branch.id,
        'name': branch.name
    } for branch in branches]
    
    return jsonify(result)

@app.route('/reorder_choices/<int:list_id>', methods=['POST'])
def reorder_choices(list_id):
    """
    Handle reordering of choices via drag and drop
    """
    reorder_data = request.form.get('reorder_data', '[]')
    try:
        # Parse the JSON data
        choices_data = json.loads(reorder_data)
        
        # Update the positions in the database
        for choice_data in choices_data:
            choice_id = choice_data.get('choice_id')
            new_position = choice_data.get('position')
            
            if choice_id and new_position:
                choice = Choice.query.get(choice_id)
                if choice and choice.list_id == list_id:
                    choice.position = new_position
        
        db.session.commit()
        flash('List order updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating list order: {str(e)}', 'danger')
    
    return redirect(url_for('edit_list', list_id=list_id))

@app.route('/save_as_new_list/<int:list_id>', methods=['POST'])
def save_as_new_list(list_id):
    """
    Create a new list with the current order
    """
    # Get form data
    new_list_name = request.form.get('new_list_name', '').strip()
    new_list_creator = request.form.get('new_list_creator', '').strip()
    reorder_data = request.form.get('reorder_data', '[]')
    
    if not new_list_name or not new_list_creator:
        flash('List name and creator are required!', 'danger')
        return redirect(url_for('edit_list', list_id=list_id))
    
    try:
        # Get the original list
        original_list = ChoiceList.query.get_or_404(list_id)
        
        # Create a new list
        new_list = ChoiceList(
            name=new_list_name,
            creator=new_list_creator,
            is_main=False  # Never set a new list as main
        )
        db.session.add(new_list)
        db.session.commit()
        
        # Parse the reorder data if available
        choices_data = json.loads(reorder_data)
        if choices_data:
            # Use the reorder data to create choices in the new list
            for position, choice_data in enumerate(choices_data, 1):
                choice_id = choice_data.get('choice_id')
                if choice_id:
                    # Get the original choice to duplicate its college_branch_id
                    original_choice = Choice.query.get(choice_id)
                    if original_choice:
                        new_choice = Choice(
                            list_id=new_list.id,
                            college_branch_id=original_choice.college_branch_id,
                            position=position
                        )
                        db.session.add(new_choice)
        else:
            # If no reorder data, copy choices from the original list
            original_choices = Choice.query.filter_by(list_id=original_list.id).order_by(Choice.position).all()
            for position, choice in enumerate(original_choices, 1):
                new_choice = Choice(
                    list_id=new_list.id,
                    college_branch_id=choice.college_branch_id,
                    position=position
                )
                db.session.add(new_choice)
        
        db.session.commit()
        flash(f'New list "{new_list_name}" created successfully!', 'success')
        return redirect(url_for('edit_list', list_id=new_list.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating new list: {str(e)}', 'danger')
        return redirect(url_for('edit_list', list_id=list_id))

@app.route('/update_cutoff_rank/<int:branch_id>', methods=['POST'])
def update_cutoff_rank(branch_id):
    college_branch = CollegeBranch.query.get_or_404(branch_id)
    is_na = 'is_na' in request.form
    
    if is_na:
        college_branch.cutoff_rank = None
        db.session.commit()
        flash('Cutoff rank set to NA successfully!', 'success')
    else:
        new_cutoff_rank = request.form.get('cutoff_rank', type=int)
        
        if new_cutoff_rank is not None:
            college_branch.cutoff_rank = new_cutoff_rank
            db.session.commit()
            flash('Cutoff rank updated successfully!', 'success')
        else:
            flash('Invalid cutoff rank value!', 'danger')
    
    return redirect(url_for('colleges'))

@app.route('/delete_college_branch/<int:branch_id>', methods=['POST'])
def delete_college_branch(branch_id):
    college_branch = CollegeBranch.query.get_or_404(branch_id)
    
    # Get college info for the flash message
    college = College.query.get(college_branch.college_id)
    branch = Branch.query.get(college_branch.branch_id)
    
    # Find any choices that use this college branch
    choices = Choice.query.filter_by(college_branch_id=branch_id).all()
    
    # Delete the choices first
    for choice in choices:
        list_id = choice.list_id
        position = choice.position
        
        # Get all choices with higher positions in the same list
        higher_choices = Choice.query.filter(
            Choice.list_id == list_id,
            Choice.position > position
        ).all()
        
        # Delete the choice
        db.session.delete(choice)
        
        # Update positions of remaining choices
        for c in higher_choices:
            c.position -= 1
    
    # Now delete the college branch
    db.session.delete(college_branch)
    db.session.commit()
    
    flash(f'Branch "{branch.name}" has been removed from "{college.name}"', 'success')
    return redirect(url_for('colleges'))

@app.route('/delete_college/<int:college_id>', methods=['POST'])
def delete_college(college_id):
    college = College.query.get_or_404(college_id)
    
    # Check if the college has any branches
    if len(college.branches) > 0:
        flash(f'Cannot delete college "{college.name}" because it has branches. Remove all branches first.', 'danger')
        return redirect(url_for('colleges'))
    
    # Delete the college
    college_name = college.name
    db.session.delete(college)
    db.session.commit()
    
    flash(f'College "{college_name}" has been deleted successfully', 'success')
    return redirect(url_for('colleges'))

@app.route('/clear_database', methods=['POST'])
def clear_database():
    # Password validation - hardcoded for simplicity
    password = request.form.get('password', '')
    
    if password != '12345':
        flash('Incorrect password. Database was not cleared.', 'danger')
        return redirect(url_for('colleges'))
    
    try:
        # Delete all data in reverse order of dependency
        Choice.query.delete()
        ChoiceList.query.delete()
        CollegeBranch.query.delete()
        College.query.delete()
        
        # We'll keep the branches table intact for the default branches
        # Branch.query.delete()
        
        # Commit the changes
        db.session.commit()
        
        # Re-add default branches
        for branch_name in DEFAULT_BRANCHES:
            branch = Branch.query.filter_by(name=branch_name).first()
            if not branch:
                branch = Branch(name=branch_name)
                db.session.add(branch)
        
        db.session.commit()
        
        flash('Database has been cleared successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing database: {str(e)}', 'danger')
    
    return redirect(url_for('colleges'))

# Initialize database
with app.app_context():
    db.create_all()
    
    # Add default branches if they don't exist
    for branch_name in DEFAULT_BRANCHES:
        branch = Branch.query.filter_by(name=branch_name).first()
        if not branch:
            branch = Branch(name=branch_name)
            db.session.add(branch)
    
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True) 