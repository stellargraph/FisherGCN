from layers import *
from metrics import *

flags = tf.app.flags
FLAGS = flags.FLAGS

class Model(object):
    def __init__(self, **kwargs):
        allowed_kwargs = { 'name', 'logging', 'input_rows', 'diag_tensor' }
        for kwarg in kwargs.keys():
            assert kwarg in allowed_kwargs, 'Invalid keyword argument: ' + kwarg
        name = kwargs.get('name')
        if not name:
            name = self.__class__.__name__.lower()
        self.name = name

        logging = kwargs.get('logging', False)
        self.logging = logging

        self.vars = {}
        self.placeholders = {}

        self.layers = []

        self.inputs = None
        self.outputs = None

        self.loss = 0
        self.accuracy = 0
        self.optimizer = None
        self.opt_op = None

    def _build(self):
        raise NotImplementedError

    def build(self):
        """ Wrapper for _build() """
        with tf.variable_scope(self.name):
            self._build()

        # Build sequential layer model
        _activations = [ self.inputs ]
        for layer in self.layers:
            hidden = layer( _activations[-1] )
            _activations.append( hidden )
        self.outputs = _activations[-1]

        # Store model variables for easy access
        variables = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name)
        self.vars = {var.name: var for var in variables}

        # Build metrics
        self._loss()
        self._accuracy()

        self.opt_op = self.optimizer.minimize(self.loss)

    def predict(self):
        pass

    def _loss(self):
        raise NotImplementedError

    def _accuracy(self):
        raise NotImplementedError

    def save(self, sess=None):
        if not sess:
            raise AttributeError("TensorFlow session not provided.")
        saver = tf.train.Saver(self.vars)
        save_path = saver.save(sess, "tmp/%s.ckpt" % self.name)
        print("Model saved in file: %s" % save_path)

    def load(self, sess=None):
        if not sess:
            raise AttributeError("TensorFlow session not provided.")
        saver = tf.train.Saver(self.vars)
        save_path = "tmp/%s.ckpt" % self.name
        saver.restore(sess, save_path)
        print("Model restored from file: %s" % save_path)


class MLP(Model):
    def __init__(self, placeholders, input_dim, **kwargs):
        super(MLP, self).__init__(**kwargs)

        self.inputs = placeholders['features']
        self.input_dim = input_dim
        # self.input_dim = self.inputs.get_shape().as_list()[1]  # To be supported in future Tensorflow versions
        self.output_dim = placeholders['labels'].get_shape().as_list()[1]
        self.placeholders = placeholders

        self.optimizer = tf.train.AdamOptimizer( learning_rate=FLAGS.learning_rate )

        self.build()

    def _loss(self):
        # Weight decay loss
        for var in self.layers[0].vars.values():
            self.loss += FLAGS.weight_decay * tf.nn.l2_loss(var)

        # Cross entropy error
        self.loss += masked_softmax_cross_entropy(self.outputs, self.placeholders['labels'],
                                                  self.placeholders['labels_mask'])

    def _accuracy(self):
        self.accuracy = masked_accuracy(self.outputs, self.placeholders['labels'],
                                        self.placeholders['labels_mask'])

    def _build(self):
        self.layers.append(Dense(input_dim=self.input_dim,
                                 output_dim=FLAGS.hidden1,
                                 placeholders=self.placeholders,
                                 act=tf.nn.relu,
                                 dropout=True,
                                 sparse_inputs=True,
                                 logging=self.logging))

        self.layers.append(Dense(input_dim=FLAGS.hidden1,
                                 output_dim=self.output_dim,
                                 placeholders=self.placeholders,
                                 act=lambda x: x,
                                 dropout=True,
                                 logging=self.logging))

    def predict(self):
        return tf.nn.softmax(self.outputs)


class GCN( Model ):
    def __init__(self, placeholders, input_dim, input_rows, diag_tensor=False, perturbation=None, subgraphs=None, **kwargs):
        super(GCN, self).__init__(**kwargs)

        self.inputs = placeholders['features']
        #self.input_rows, self.input_dim = self.inputs.get_shape().as_list()
        self.input_dim  = input_dim
        self.input_rows = input_rows
        self.output_dim = placeholders['labels'].get_shape().as_list()[1]
        self.placeholders = placeholders
        self.perturbation = perturbation
        self.subgraphs = subgraphs

        self.optimizer = tf.train.AdamOptimizer( learning_rate=FLAGS.learning_rate )

        self.diag_tensor = diag_tensor
        self.build()

    def build(self):
        """ Wrapper for _build() """

        with tf.variable_scope( self.name ):
            self._build()

        if self.perturbation is None:
            _activations = [ self.inputs ]
            for layer in self.layers:
                _activations.append( layer(_activations[-1]) )
            self.outputs = _activations[-1]

        else:
            self.outputs = []
            for i in range( FLAGS.fisher_perturbation ):
                _activations = self.inputs
                for layer in self.layers:
                    _activations =  layer( _activations, i )
                self.outputs.append( _activations )

        # Store model variables for easy access
        variables = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name)
        self.vars = {var.name: var for var in variables}

        # Build metrics
        self._loss()
        self._accuracy()

        grads_vars = self.optimizer.compute_gradients( self.loss, tf.trainable_variables() )
        def gan( grads_vars ):
           for grad, var in grads_vars:
               if 'perturb' in var.name and FLAGS.fisher_adversary == 1:
                    yield( (-grad,var) )
               else:
                   yield( (grad,var) )
        self.opt_op = self.optimizer.apply_gradients( gan(grads_vars) )

        # if self.perturbation is not None and FLAGS.fisher_adversary > 0:
            # def adv_grads( grads_vars ):
               # for grad, var in grads_vars:
                   # if 'perturb' in var.name:   # and FLAGS.fisher_adversary == 1:
                        # yield( (-grad,var) )
                   # else:
                        # pass
            # self.adv_op = self.optimizer.apply_gradients( adv_grads(self.optimizer.compute_gradients( self.fisherloss, tf.trainable_variables() ) ) )

    def _loss( self ):
        # l1_regularizer = tf.contrib.layers.l1_regularizer( scale=0.00008, scope=None )
        # weights = tf.trainable_variables() # all vars of your graph
        # self.loss += tf.contrib.layers.apply_regularization( l1_regularizer, weights )

        for var in tf.trainable_variables():
            if not 'perturbation' in var.name:
                self.loss += FLAGS.weight_decay * tf.nn.l2_loss(var)

        # Cross entropy error
        if self.perturbation is None:
            self.loss += masked_softmax_cross_entropy( self.outputs,
                                                       self.placeholders['labels'],
                                                       self.placeholders['labels_mask'] )

        else:
            #_larray = tf.stack( [ o-tf.reduce_logsumexp(o, axis=1, keepdims=True) for o in self.outputs ] )
            #_pred = tf.reduce_logsumexp( _larray, axis=0 )
            #crossent = -tf.reduce_sum( _pred * self.placeholders['labels'], axis=1 )
            #mask = tf.cast( self.placeholders['labels_mask'], dtype=tf.float32 )
            #self.loss += tf.reduce_sum( crossent * mask ) / tf.reduce_sum( mask ) + np.log(FLAGS.fisher_perturbation)

            _larray = tf.stack( [ masked_softmax_cross_entropy( o, self.placeholders['labels'], self.placeholders['labels_mask'] ) for o in self.outputs ] )
            mean_loss = tf.reduce_mean( _larray )
            self.loss += mean_loss

    def _accuracy( self ):
        if self.perturbation is None:
            self.accuracy = masked_accuracy( self.outputs, self.placeholders['labels'],
                                             self.placeholders['labels_mask'] )

        else:
            out = tf.reduce_mean( tf.stack( [ tf.nn.softmax(o, axis=1) for o in self.outputs ] ), axis=0 )
            self.accuracy = masked_accuracy( out, self.placeholders['labels'],
                                             self.placeholders['labels_mask'] )

    def _build(self):
        layer1 = GraphConvolution( input_dim=self.input_dim,
                                   input_rows=self.input_rows,
                                   output_dim=FLAGS.hidden1,
                                   placeholders=self.placeholders,
                                   act=tf.nn.relu,
                                   dropout=True,
                                   sparse_inputs=True,
                                   diag_tensor=self.diag_tensor,
                                   perturbation=self.perturbation,
                                   logging=self.logging )
        layer2 = GraphConvolution( input_dim=FLAGS.hidden1,
                                   input_rows=self.input_rows,
                                   output_dim=self.output_dim,
                                   placeholders=self.placeholders,
                                   act=lambda x: x,
                                   dropout=True,
                                   diag_tensor=self.diag_tensor,
                                   perturbation=self.perturbation,
                                   logging=self.logging )
        layer1.subgraphs = layer2.subgraphs = self.subgraphs
        self.layers.append( layer1 )
        self.layers.append( layer2 )

    def predict(self):
        return tf.nn.softmax( self.outputs )

