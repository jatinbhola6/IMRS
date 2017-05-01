from flask import Flask, jsonify, abort, make_response, render_template,request,Response,url_for,redirect
from flask_restful import reqparse, Api, Resource
from werkzeug.datastructures import Headers
import pymongo
import utility
import ast
import requests
from lxml import html
import ast
from itsdangerous import TimedJSONWebSignatureSerializer as SS
from itsdangerous import BadSignature,SignatureExpired
util = utility.Utilities()
parser = reqparse.RequestParser()
parser.add_argument('info')
app = Flask(__name__)
app.config.update(dict(SECRET_KEY='AKADBAKADBAMBEBO'))
api = Api(app)
def gen_auth_token(args):
    s = SS(app.config['SECRET_KEY'],expires_in = 3600)
    return s.dumps(args)
def verify_token(user_id,token):
    s = SS(app.config['SECRET_KEY'])
    try:
        obj = s.loads(token)
        print obj,user_id
        return obj['user_id'] == user_id
    except BadSignature:
        return 'Cannot Authorize'
    except SignatureExpired:
        return 'Session Expired. Sign In Again'
def get_collection(db_name='test_database',coll_name='test_collection'):
    conn = pymongo.MongoClient()
    db = conn[db_name]
    coll = db[coll_name]
    return coll

def auth(uname,pword):
    coll = get_collection(coll_name='Users')
    res = (coll.find_one({'user_name':uname,'password':pword}))
    if res:
        return res,gen_auth_token({'user_id':str(res['_id']),'password':pword})
    else:
        return False
def get_movie_details(movie_id_list):
    movie_coll = get_collection()
    top_movie_list = []
    for movie in movie_id_list:
        movie_detail = movie_coll.find_one({"movie id":ast.literal_eval(movie)})
        if movie_detail['img_url'] == '':
            movie_detail['img_url'] =url_for('static',filename='blank.png')
        top_movie_list.append(movie_detail)
    return top_movie_list

class HomePage(Resource):
    def get(self):
        msg = request.args.get('msg')
        return dict(linkForAjax=url_for('getMore'),page_type='index_page',index=-8,msg=msg)

class Login(Resource):
    def post(self):
        uname = request.form['username']
        pword = request.form['password']
        if uname is None or pword is None:
            return redirect(url_for('homepage',msg="Fill all field"))
        (res,token) = auth(uname,pword)
        if res:
            return redirect(url_for('mainpage',user_id=res['_id'],token=token))
        else:
            return redirect(url_for('homepage',msg="Username or Password Incorect"))
class MainPage(Resource):
    def get(self):
        res_id = request.args.get('user_id')
        token = request.args.get('token')
        obj = verify_token(res_id,token)
        if obj == True:
            return dict(linkForAjax=url_for('getMore'),page_type='main_page',index=-8,user_id=res_id,token=token,page_type='main_page')
        else:
            return abort(400)
class SignUp(Resource):
    def post(self):
        user_details = request.form.to_dict()
        if user_details['name'] is '' or user_details['user_name'] is '' or user_details['password'] is '' or user_details['email'] is '':
            return redirect(url_for('homepage',msg="Fill all field"))
        coll = get_collection(coll_name = 'Users')
        if bool(coll.find_one({'user_name':user_details['user_name']})):
            return redirect(url_for('homepage',msg="User already exists"))
        cur = coll.aggregate([{"$group":{"_id":"","max_id":{"$max":"$_id"}}}])
        for item in cur:
            max_id = item["max_id"]
        user_details['_id'] = max_id+1
        coll.insert_one(user_details)
        token = gen_auth_token({'user_id':str(user_details['_id']),'password':user_details['password']})
        resp = redirect(url_for('feedback',user_id=user_details['_id'],token=token,new=True))
        return resp

class Feedback(Resource):
    def get(self):
        res_id = request.args.get('user_id')
        token = request.args.get('token')
        obj = verify_token(res_id,token)
        if obj == True:
            return dict(linkForAjax=url_for('getMore'),page_type='main_page',index=-8,user_id=res_id,token=token,page_type='feed_page')
        else:
            return abort(400)

class MovieInfo(Resource):
    def get(self):
        movie_detail = get_movie_details([request.args.get('mid')])
        user_id = request.args.get('user_id')
        token = request.args.get('token')
        return dict(movie=movie_detail[0],index=-8,no_recom=8,token=token,user_id=user_id,linkForAjax=url_for('getMore'),page_type='movie_page')

class newRatings(Resource):
    def post(self):
        res = request.form.get('user_id')
        obj = verify_token(res,request.form.get('token'))
        if obj == True:
            rating = request.form.get('rate')
            user_id = request.form.get('user_id')
            movie_id = request.form.get('mid')
            util.add_rating(ast.literal_eval(user_id),ast.literal_eval(rating),(movie_id))
            return ({},200,None)
        else:
            return redirect(url_for('homepage',msg=obj))

@app.route('/getMore',methods=['POST',"GET"])
def getMore():
    page_type = request.form.get('page_type')
    index = request.form.get('index')
    res = request.form.get('user_id')
    mid = request.form.get('mid')
    no_recom = 8 if request.form.get('no_recom') is None else request.form.get('no_recom')
    if page_type == 'index_page':
        top_movies = util.get_top_movies(index=int(index))
        top_movie_list = get_movie_details(top_movies)
        return dict(movies=top_movie_list)
    elif page_type == 'main_page':
        obj = verify_token(res,request.form.get('token'))
        if obj == True:
            recom_movies = util.get_recommendations(user_id=int(res),index=int(index))
            recom_movie_list = get_movie_details(recom_movies)
            return dict(movies=recom_movie_list,user_id=res,token=request.form.get('token'))
        else:
            return redirect(url_for('homepage',msg=obj))
    elif page_type == 'feed_page':
        #if not res:
        movies = util.get_top_movies(index=int(index),num_movies=int(no_recom))
        movie_list = get_movie_details(movies)
        return dict(movies=movie_list,user_id=res,token=request.form.get('token'))
    elif page_type == 'movie_page':
        movies = util.get_similar_movies(mid,index=int(index),no_recom=int(no_recom))
        movies_info = get_movie_details(movies)
        if res is not None and request.form.get('token') is not None:
            return dict(movies=movies_info,user_id=res,token=request.form.get('token'))
        else:
            return dict(movies=movies_info)
    else:
        return redirect(url_for('homepage',msg="400 Bad Request"))


api.add_resource(HomePage,'/')
api.add_resource(Login,'/login')
api.add_resource(SignUp,'/signup')
api.add_resource(Feedback,'/feedpage')
api.add_resource(newRatings,'/newrating')
api.add_resource(MainPage,'/mainpage')
api.add_resource(MovieInfo,'/movie')
if __name__ == '__main__':
    app.run(debug=True)
