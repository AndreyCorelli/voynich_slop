#include <cmath>
#include <vector>
extern "C" void score_segments(const int* assignments, const int* words,
 const int* starts, const int* ends, const int* selected, int count,
 const int* offsets, const int* states, const double* weights,
 const double* transition, int state_count, int bos, int eos, double* result) {
 std::vector<double> previous(state_count), current(state_count);
 for(int n=0;n<count;++n){
  int segment=selected[n];
  int previous_start=-1, previous_end=-1; previous[0]=1.;
  double score=0.;
  for(int pos=starts[segment];pos<=ends[segment];++pos){
   bool finish=pos==ends[segment];
   int profile=finish ? -1 : assignments[words[pos]];
   int begin=finish ? 0 : offsets[profile], end=finish ? 1 : offsets[profile+1];
   double normalization=0.;
   for(int k=begin;k<end;++k){
    int b=finish ? eos : states[k]; double value=0.;
    if(previous_start<0) value=transition[bos*state_count+b];
    else for(int j=previous_start;j<previous_end;++j)
      value+=previous[j-previous_start]*transition[states[j]*state_count+b];
    current[k-begin]=value*(finish ? 1. : weights[k]);
    normalization+=current[k-begin];
   }
   score+=std::log(normalization);
   for(int k=begin;k<end;++k) previous[k-begin]=current[k-begin]/normalization;
   previous_start=begin; previous_end=end;
  }
  result[n]=score;
 }
}
