#include "stats.h"
#include <cmath>


Stats::Stats(bool get_dist)
{
    this->sum = 0;
    this->sq_sum = 0;
    this->count = 0;
    this->get_dist = get_dist;
}


void Stats::input_data(double data){
    sum += data;
    sq_sum += data * data;
    count++;
}

void Stats::input_data(int data){
    input_data((double)data);
}

void Stats::operator+=(const double &data){
    input_data(data);
}
void Stats::operator+=(const int &data)
{
    input_data(data);
}


double Stats::avg(){
    return sum/count;
}

double Stats::size(){
    return count;
}

double Stats::sd(){
    return sqrt(sq_sum/count - avg() * avg());
}

double Stats::total(){
    return sum;
}

void Stats::set_precision()
{

}

