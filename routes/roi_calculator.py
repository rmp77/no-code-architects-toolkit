from flask import Blueprint, send_file
import os

roi_calculator_bp = Blueprint('roi_calculator', __name__)


@roi_calculator_bp.route('/roi')
def roi_calculator():
    html_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'roi_calculator.html'
    )
    return send_file(os.path.abspath(html_path))
