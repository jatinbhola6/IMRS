import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
class ALS_algo():
	def get_error(self,Q, X, Y, W):
		#return mean error of predictions
		return np.sum((W * (Q - np.dot(X, Y)))**2)
	def get_W(self,Q):
			W = Q>0.5	
			W[W == True] = 1
			W[W == False] = 0
			W = W.astype(np.float64,copy = False)
			return W
	def get_weighted_factors(self,file_name = 'u1.base1',X_file='X.npy',Y_file='Y.npy',lambda_ = 0.1,n_factors = 100,n_iterations = 20,max_rating=5):
		#Alternating Least Squares Algorithm
		#for reference visit - https://bugra.github.io/work/notes/2014-04-19/alternating-least-squares-method-for-collaborative-filtering/ 
		ratings = pd.read_csv('ml-100k/'+ file_name)
		Q = ratings.loc[:,str(1):].values
		W = self.get_W(Q)
		m, n = Q.shape
		X = max_rating * np.random.rand(m, n_factors) 
		Y = max_rating * np.random.rand(n_factors, n)
		weighted_errors = []
		for ii in range(n_iterations):
			for u, Wu in enumerate(W):
				X[u] = np.linalg.solve(np.dot(Y, np.dot(np.diag(Wu), Y.T)) + lambda_ * np.eye(n_factors),np.dot(Y, np.dot(np.diag(Wu), Q[u].T))).T
			for i, Wi in enumerate(W.T):
				Y[:,i] = np.linalg.solve(np.dot(X.T, np.dot(np.diag(Wi), X)) + lambda_ * np.eye(n_factors),np.dot(X.T, np.dot(np.diag(Wi), Q[:, i])))
			weighted_errors.append(self.get_error(Q, X, Y, W))
			print('{}th iteration is completed'.format(ii))
		weighted_Q_hat = np.dot(X,Y)
		#np.save('q_hat',weighted_Q_hat)
		np.save(X_file,X)
		np.save(Y_file,Y)

	def get_recommendations(self,user_id,no_recom=5,max_rating=5,X_file='X.npy',Y_file='Y.npy',file_name = 'u1.base1'):
		#call this to get recommendations
		#User ID is necessary argument.
		X = np.load(X_file)
		Y = np.load(Y_file)
		ratings = pd.read_csv('ml-100k/'+ file_name)
		Q = ratings.loc[:,str(1):].values
		W = self.get_W(Q)
		user_index = user_id-1
		Q_hat = np.dot(X,Y)[user_index]
		Q_hat -= np.min(Q_hat)
		Q_hat *= float(max_rating) / np.max(Q_hat)
		top_recommendations = np.argsort(Q_hat-max_rating*W[user_id-1])[::-1][:no_recom]
		movie_data = pd.read_csv('test.csv')
		movie_ids = [movie_data.iloc[i]['_id'] for i in top_recommendations]
		return movie_ids
	def stream_ALS(self,user_id,movie_id,rating,file_name='u1.base1',X_file='X.npy',Y_file='Y.npy',lambda_=0.1):
		#call this when new rating is recieved in the database.
		#for reference visit - https://stanford.edu/~rezab/classes/cme323/S15/notes/lec14.pdf
		X = np.load(X_file)
		Y = np.load(Y_file)
		ratings = pd.read_csv('ml-100k/'+ file_name)
		movie_index = ratings.columns.get_loc(str(movie_id))
		user_index = user_id-1
		Xu = X[user_index]
		Yi = Y[:,movie_index]
		Xu_ = Xu - (rating - np.dot(Xu,Yi))*Yi.T*lambda_ + lambda_*Xu
		Yi_ = Yi - (rating-np.dot(Xu,Yi))*Xu.T*lambda_ + lambda_*Yi
		X[user_index] = Xu_
		Y[:,movie_index] = Yi_
		np.save(X_file,X)
		np.save(Y_file,Y)

if __name__ == '__main__':
	ob = ALS_algo()
	print ob.get_recommendations(7)