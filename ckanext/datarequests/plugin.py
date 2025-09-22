import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from .model import setup as model_setup
from .logic import action as actions
from .logic import auth as auth_functions
from flask import Blueprint, request, redirect
from ckan.model import Session
from .model import DataRequest

log = logging.getLogger(__name__)


class DataRequestsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    def update_config(self, config):
        # Templates & public
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')

        # DB model setup (lazy create)
        try:
            model_setup()
        except Exception as e:
            log.warning("ckanext-datarequests: model setup warning: %r", e)

    # Actions
    def get_actions(self):
        return {
            'datarequest_create': actions.datarequest_create,
            'datarequest_show': actions.datarequest_show,
            'datarequest_list': actions.datarequest_list,
            'datarequest_comment_create': actions.datarequest_comment_create,
            'datarequest_comment_list': actions.datarequest_comment_list,
            'datarequest_status_update': actions.datarequest_status_update,
        }

    # Auth
    def get_auth_functions(self):
        return {
            'datarequest_create': auth_functions.datarequest_create,
            'datarequest_show': auth_functions.datarequest_show,
            'datarequest_list': auth_functions.datarequest_list,
            'datarequest_comment_create': auth_functions.datarequest_comment_create,
            'datarequest_comment_list': auth_functions.datarequest_comment_list,
            'datarequest_status_update': auth_functions.datarequest_status_update,
        }

    # Blueprint / Routes
    def get_blueprint(self):
        bp = Blueprint('datarequests', __name__)

        @bp.route('/datarequests')
        def index():
            # Yorumları da içerecek şekilde liste
            try:
                reqs = tk.get_action('datarequest_list')(
                    {'ignore_auth': True},
                    {'include_comments': True}
                )
            except Exception as e:
                tk.h.flash_error(
                    tk._('Veri istekleri yüklenemedi: {0}').format(e))
                reqs = []
            return tk.render('datarequests/index.html', extra_vars={
                'datarequests': reqs,
                'is_authenticated': bool(tk.c.user),
            })

        @bp.route('/datarequests/new', methods=['GET', 'POST'])
        def new():
            if not tk.c.user:
                tk.h.flash_error(
                    tk._('Lütfen giriş yapın. Veri isteği oluşturmak için giriş gerekli.'))
                return redirect(tk.h.url_for('user.login'))

            if request.method == 'POST':
                title = request.form.get('title', '').strip()
                description = request.form.get('description', '').strip()
                try:
                    created = tk.get_action('datarequest_create')(
                        {'user': tk.c.user},
                        {'title': title, 'description': description}
                    )
                    tk.h.flash_success(tk._('Veri isteği oluşturuldu.'))
                    return redirect(tk.h.url_for('datarequests.show', id=created['id']))
                except tk.ValidationError as e:
                    tk.h.flash_error(tk._('Hata: {0}').format(e.error_dict))
                except Exception as e:
                    tk.h.flash_error(
                        tk._('Veri isteği oluşturulamadı: {0}').format(e))
            return tk.render('datarequests/new.html', extra_vars={})

        @bp.route('/datarequests/<id>')
        def show(id):
            # Tekil data request
            try:
                dr = tk.get_action('datarequest_show')({}, {'id': id})
            except Exception as e:
                tk.abort(404, tk._('Veri isteği bulunamadı: {0}').format(e))

            # Şimdilik eski yöntemle ilişkiden çekiyoruz
            data_request = Session.query(DataRequest).get(id)
            comments = data_request.comments if data_request else []

            return tk.render('datarequests/show.html', extra_vars={
                'dr': dr,
                'comments': comments,
                'is_authenticated': bool(tk.c.user),
                'is_sysadmin': bool(getattr(tk.c, 'userobj', None) and getattr(tk.c.userobj, 'sysadmin', False)),
            })

        @bp.route('/datarequests/<id>/comments', methods=['POST'])
        def add_comment(id):
            if not tk.c.user:
                tk.h.flash_error(tk._('Yorum yapmak için giriş yapmalısınız.'))
                return redirect(tk.h.url_for('user.login'))

            content = request.form.get('content', '').strip()
            try:
                tk.get_action('datarequest_comment_create')(
                    {'user': tk.c.user},
                    {'data_request_id': id, 'content': content}
                )
                tk.h.flash_success(tk._('Yorum eklendi.'))
            except tk.ValidationError as e:
                tk.h.flash_error(tk._('Hata: {0}').format(e.error_dict))
            except Exception as e:
                tk.h.flash_error(tk._('Yorum eklenemedi: {0}').format(e))
            return redirect(tk.h.url_for('datarequests.show', id=id))

        @bp.route('/datarequests/<id>/status', methods=['POST'])
        def change_status(id):
            if not tk.c.user:
                tk.h.flash_error(
                    tk._('Durum değiştirmek için giriş yapmalısınız.'))
                return redirect(tk.h.url_for('user.login'))

            status = request.form.get('status', '').strip()
            try:
                tk.get_action('datarequest_status_update')(
                    {'user': tk.c.user},
                    {'id': id, 'status': status}
                )
                tk.h.flash_success(tk._('Durum güncellendi.'))
            except tk.NotAuthorized:
                tk.h.flash_error(tk._('Bu işlem için yetkiniz yok.'))
            except tk.ValidationError as e:
                tk.h.flash_error(tk._('Hata: {0}').format(e.error_dict))
            except Exception as e:
                tk.h.flash_error(tk._('Durum güncellenemedi: {0}').format(e))
            return redirect(tk.h.url_for('datarequests.show', id=id))

        return bp
