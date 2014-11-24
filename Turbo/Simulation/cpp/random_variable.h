#ifndef RANDOM_VARIABLE_H
#define RANDOM_VARIABLE_H


class UniformRandomVariable {
public:
  double value();
  UniformRandomVariable();
  UniformRandomVariable(double min, double max);
  double min_;
  double max_;
};


class ExponentialRandomVariable {
public:
  double value();
  ExponentialRandomVariable(double avg);
  double avg_;
  UniformRandomVariable urv;
};



struct CDFentry {
  double cdf_;
  double val_;
};


class EmpiricalRandomVariable {
public:
  double value();
  double interpolate(double u, double x1, double y1, double x2, double y2);

  EmpiricalRandomVariable(std::string filename);
  int loadCDF(std::string filename);

protected:
  int lookup(double u);

  double minCDF_;		// min value of the CDF (default to 0)
  double maxCDF_;		// max value of the CDF (default to 1)
  int numEntry_;		// number of entries in the CDF table
  int maxEntry_;		// size of the CDF table (mem allocation)
  CDFentry* table_;	// CDF table of (val_, cdf_)
};


#endif
