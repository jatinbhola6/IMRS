# coding=UTF-8 
import pandas as pd
import numpy as np
import ast
from sklearn.metrics.pairwise import cosine_similarity
class CB_Filtering():
	def converting_to_dummy_variable(self,file_name = 'test.csv',movie_features=['_id','director','creator','actor_list','genre'],out_file='dummy_data_for_clustering.csv'):
		#this method converts data features to dummy features
		"""
		  _______________					 ___________
	   	 |A_____|B_______|  is converted to |a|b|c|d|e|f| 
	   	1|a,b___|d,f_____|				   1|1|1|0|1|0|1|
		2|b,c___|d,e_____|				   2|0|1|1|1|1|0|
		"""
		print "reading file"
		movie_data = pd.read_csv(file_name,usecols = movie_features)
		movie_data[movie_features] = movie_data[movie_features].apply(lambda x:x.str.replace('“','"')).apply(lambda x:x.str.replace('”','"'))
		print movie_data
		movie_data[movie_features[1:]] = movie_data[movie_features[1:]].applymap(lambda x:ast.literal_eval(x))
		dummy_data = pd.DataFrame(movie_data[['_id']])
		for feature in movie_features[1:]:
			dummy_data = dummy_data.merge(movie_data[feature].str.join(sep='|').str.get_dummies(sep='|'),left_index=True,right_index=True)
		dummy_data.to_csv(out_file)

	def similarity_matrix(self,file_name='dummy_data_for_clustering.csv',def_index='_id',sim_file='similarity_matrix.npy'):
		#this calculates similarty of each movie with each movie
		#if m = number of movies and f = no. of features
		#and our data is of form mxf then it gives us a 2d matrix of form mxm 
		dummy_data = pd.read_csv(file_name)
		dummy_data = dummy_data.iloc[:,1:].set_index(def_index)	
		distances = cosine_similarity(dummy_data,dummy_data)
		np.save(sim_file,distances)

	def get_recommendations(self,movie_id,sim_file='similarity_matrix.npy',movie_file='test.csv',no_recom=5):
		#it gives recommendations from movie id.
		#Movie ID is necesssary argument for this recommendation
		cos_sim = np.load(sim_file)
		movie_list = pd.read_csv(movie_file)
		movie_index = movie_list.index.get_loc(movie_list[movie_list._id == movie_id].iloc[0].name)
		top_recommendations = np.argsort(cos_sim[movie_index])[::-1][1:6]
		recom_ids = [movie_list.iloc[i]['_id'] for i in top_recommendations]
		return recom_ids

	def add_new_movie(self,movie_id,movie_file='test.csv',movie_features=['_id','director','creator','actor_list','genre'],dummy_file = 'dummy_data_for_clustering.csv'):
		#this functions add new movie entries in our database to our dataframes. 
		print _file
		if not hasattr(movie_id,'__iter__') :
			movie_id = [movie_id]
		else:
			movie_id = list(movie_id)
		movie_data = pd.read_csv(movie_file)
		new_df = movie_data.loc[movie_id]
		new_df[movie_features] = new_df[movie_features].apply(lambda x:x.str.replace('“','"')).apply(lambda x:x.str.replace('”','"'))
		new_df[movie_features] = new_df[movie_features].applymap(lambda x:ast.literal_eval(x))
		dummy_data = pd.DataFrame(new_df[['_id']])
		for feature in movie_features[1:]:
			dummy_data = dummy_data.merge(new_df[feature].str.join(sep='|').str.get_dummies(sep='|'),left_index=True,right_index=True)
		old_dummy = pd.DataFrame(_file)
		old_dummy = old_dummy.append(dummy_data)
		old_dummy.to_csv(dummy_file)
if __name__ == "__main__":
	ob = CB_Filtering()
	print ob.get_recommendations('tt0114709')
